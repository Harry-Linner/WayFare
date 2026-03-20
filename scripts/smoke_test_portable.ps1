#requires -Version 5.1
Add-Type -AssemblyName System.Net.Http

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$BundleDir = Join-Path $Root "release\WayFare-MVP-Portable"
$ExePath = Join-Path $BundleDir "WayFare.exe"
$BundledAIBackendDir = Join-Path $BundleDir "wayfare_ai_backend"
$TestDir = Join-Path $Root "release\portable-smoke-test"
$TestExePath = Join-Path $TestDir "WayFare.exe"
$TestAIBackendDir = Join-Path $TestDir "wayfare_ai_backend"
$Port = 37881
$FeedbackLogPath = Join-Path $TestDir "data\feedback.jsonl"

if (-not (Test-Path $ExePath)) {
  throw "WayFare.exe not found. Run scripts/build_portable.ps1 first."
}

if (Test-Path $TestDir) {
  Remove-Item $TestDir -Recurse -Force
}
New-Item -ItemType Directory -Force $TestDir | Out-Null
Copy-Item $ExePath $TestExePath -Force
if (Test-Path $BundledAIBackendDir) {
  Copy-Item $BundledAIBackendDir $TestAIBackendDir -Recurse -Force
}

function Start-WayFare {
  $env:WAYFARE_OPEN_BROWSER = '0'
  $env:WAYFARE_PORT = "$Port"
  return Start-Process -FilePath $TestExePath -WorkingDirectory $TestDir -PassThru
}

function Wait-ForHealth {
  param([int]$TimeoutSeconds = 20)

  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    try {
      $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/healthz"
      if ($health.status -eq "ok") {
        return
      }
    }
    catch {
      Start-Sleep -Milliseconds 500
    }
  }

  throw "WayFare portable server did not become healthy within $TimeoutSeconds seconds."
}

function Upload-TestFile {
  param(
    [string]$Uri,
    [string]$FilePath,
    [string]$ContentType = 'application/pdf'
  )

  $handler = New-Object System.Net.Http.HttpClientHandler
  $client = New-Object System.Net.Http.HttpClient($handler)
  try {
    $multipart = New-Object System.Net.Http.MultipartFormDataContent
    $bytes = [System.IO.File]::ReadAllBytes($FilePath)
    $fileContent = New-Object System.Net.Http.ByteArrayContent -ArgumentList (,[byte[]]$bytes)
    $fileContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse($ContentType)
    $multipart.Add($fileContent, 'file', [System.IO.Path]::GetFileName($FilePath))
    $response = $client.PostAsync($Uri, $multipart).Result
    if (-not $response.IsSuccessStatusCode) {
      throw "Upload failed with status $($response.StatusCode)"
    }
    return ($response.Content.ReadAsStringAsync().Result | ConvertFrom-Json)
  }
  finally {
    $client.Dispose()
  }
}

$proc = $null

try {
  $proc = Start-WayFare
  Wait-ForHealth

  # Knowledge base flow
  $kbPayload = @{ name = 'Smoke Test KB'; description = 'Created by scripts/smoke_test_portable.ps1' } | ConvertTo-Json
  $createdKb = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/knowledge-bases" -Method Post -ContentType "application/json" -Body $kbPayload
  if (-not $createdKb.knowledgeBase.id) {
    throw 'Create knowledge base failed.'
  }
  $kbId = [string]$createdKb.knowledgeBase.id

  $kbList = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/knowledge-bases"
  if (($kbList.knowledgeBases | Measure-Object).Count -lt 1) {
    throw 'List knowledge bases failed.'
  }

  # Profile flow
  $globalProfileBody = @{ content = "# Global Profile`n`n- Preferred language: Simplified Chinese`n- Source: portable smoke test" } | ConvertTo-Json
  $savedGlobalProfile = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/profiles/global" -Method Put -ContentType "application/json" -Body $globalProfileBody
  if (-not $savedGlobalProfile.profile.content) {
    throw 'Save global profile failed.'
  }

  $loadedGlobalProfile = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/profiles/global"
  if ($loadedGlobalProfile.profile.scope -ne 'global') {
    throw 'Load global profile failed.'
  }

  $kbProfileBody = @{ content = "# Knowledge Base Profile`n`n- Goal: verify prompt profile injection during the portable smoke test." } | ConvertTo-Json
  $savedKbProfile = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/knowledge-bases/$kbId/profile" -Method Put -ContentType "application/json" -Body $kbProfileBody
  if (-not $savedKbProfile.profile.knowledgeBaseId) {
    throw 'Save knowledge base profile failed.'
  }

  $loadedKbProfile = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/knowledge-bases/$kbId/profile"
  if ($loadedKbProfile.profile.knowledgeBaseId -ne $kbId) {
    throw 'Load knowledge base profile failed.'
  }

  $pdfPath = Join-Path $TestDir 'sample.pdf'
  $pdfContent = "%PDF-1.1`n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj`n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj`n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj`ntrailer<</Root 1 0 R>>`n%%EOF"
  [System.IO.File]::WriteAllText($pdfPath, $pdfContent)

  $uploaded = Upload-TestFile -Uri "http://127.0.0.1:$Port/knowledge-bases/$kbId/documents" -FilePath $pdfPath
  if (-not $uploaded.document.id) {
    throw 'Upload document failed.'
  }
  $documentId = [string]$uploaded.document.id

  $documents = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/knowledge-bases/$kbId/documents"
  if (($documents.documents | Measure-Object).Count -lt 1) {
    throw 'List documents failed.'
  }

  $fileResponse = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/documents/$documentId/file"
  if ($fileResponse.StatusCode -ne 200) {
    throw 'Serve document failed.'
  }

  # Chat flow
  $chatBody = @{
    projectId = 1
    knowledgeBaseId = $kbId
    context = 'Please answer in Chinese and summarize the current smoke test knowledge base.'
  } | ConvertTo-Json
  $chatResponse = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/chat" -Method Post -ContentType "application/json" -Body $chatBody
  if (-not $chatResponse.content) {
    throw 'Chat request failed.'
  }

  # Feedback flow
  $feedbackBody = @{
    category = 'bug'
    sentiment = 'neutral'
    message = 'portable smoke test feedback entry'
    page = 'workspace'
    scope = 'smoke-test'
    recentAction = 'smoke_test'
    knowledgeBaseId = $kbId
    documentId = $documentId
    metadata = @{ source = 'scripts/smoke_test_portable.ps1' }
  } | ConvertTo-Json -Depth 5
  $feedbackResponse = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/feedback" -Method Post -ContentType "application/json" -Body $feedbackBody
  if (-not $feedbackResponse.ok) {
    throw 'Feedback request failed.'
  }
  if (-not (Test-Path $FeedbackLogPath)) {
    throw 'Feedback log file was not created.'
  }

  # Schedule flow
  $scheduledFor = (Get-Date).AddMinutes(8).ToUniversalTime().ToString("o")
  $createBody = @{
    title = "Smoke Test Reminder"
    description = "Created by scripts/smoke_test_portable.ps1"
    scheduledFor = $scheduledFor
    reminderOffsetMinutes = 0
    repeatRule = "none"
  } | ConvertTo-Json

  $created = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/schedules" -Method Post -ContentType "application/json" -Body $createBody
  if (-not $created.schedule.id) {
    throw "Create schedule failed."
  }

  $scheduleId = [int]$created.schedule.id
  $listed = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/schedules"
  if (($listed.schedules | Measure-Object).Count -lt 1) {
    throw "List schedules failed."
  }

  $snoozed = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/schedules/$scheduleId/snooze" -Method Post -ContentType "application/json" -Body (@{ minutes = 10 } | ConvertTo-Json)
  if (-not $snoozed.schedule.snoozedUntil) {
    throw "Snooze schedule failed."
  }

  $rescheduledTime = (Get-Date).AddMinutes(12).ToUniversalTime().ToString("o")
  $rescheduled = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/schedules/$scheduleId/reschedule" -Method Post -ContentType "application/json" -Body (@{ scheduledFor = $rescheduledTime } | ConvertTo-Json)
  $expectedDate = ([datetime]$rescheduledTime).ToUniversalTime()
  $actualDate = ([datetime]$rescheduled.schedule.scheduledFor).ToUniversalTime()
  if ([math]::Abs(($expectedDate - $actualDate).TotalSeconds) -gt 1) {
    throw "Reschedule schedule failed."
  }

  $completed = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/schedules/$scheduleId/complete" -Method Post
  if ($completed.schedule.status -ne "completed") {
    throw "Complete schedule failed."
  }

  if ($proc -and -not $proc.HasExited) {
    Stop-Process -Id $proc.Id -Force
    Start-Sleep -Seconds 1
  }

  $proc = Start-WayFare
  Wait-ForHealth

  $reloadedKb = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/knowledge-bases"
  $matchedKb = $reloadedKb.knowledgeBases | Where-Object { $_.id -eq $kbId }
  if (-not $matchedKb) {
    throw 'Knowledge base persistence check failed after restart.'
  }

  $reloadedSchedules = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/schedules"
  $matchedSchedule = $reloadedSchedules.schedules | Where-Object { [int]$_.id -eq $scheduleId }
  if (-not $matchedSchedule) {
    throw 'Schedule persistence check failed after restart.'
  }

  $reloadedGlobalProfile = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/profiles/global"
  if (-not $reloadedGlobalProfile.profile.content) {
    throw 'Global profile persistence check failed after restart.'
  }

  $reloadedKbProfile = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/knowledge-bases/$kbId/profile"
  if ($reloadedKbProfile.profile.knowledgeBaseId -ne $kbId) {
    throw 'Knowledge base profile persistence check failed after restart.'
  }

  $feedbackLines = Get-Content $FeedbackLogPath
  if (($feedbackLines | Measure-Object).Count -lt 1) {
    throw 'Feedback log persistence check failed.'
  }

  Write-Host "Portable smoke test passed."
}
finally {
  if ($proc -and -not $proc.HasExited) {
    Stop-Process -Id $proc.Id -Force
  }
}



