import * as pdfjsLib from 'pdfjs-dist/build/pdf.mjs';
import workerSrc from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import '../styles/pdf-text-layer.css';

pdfjsLib.GlobalWorkerOptions.workerSrc = workerSrc;

type PdfViewerModule = typeof import('pdfjs-dist/web/pdf_viewer.mjs');

let pdfViewerModulePromise: Promise<PdfViewerModule> | null = null;

async function loadPdfViewerModule() {
  if (!pdfViewerModulePromise) {
    (globalThis as typeof globalThis & { pdfjsLib?: typeof pdfjsLib }).pdfjsLib = pdfjsLib;
    pdfViewerModulePromise = import('pdfjs-dist/web/pdf_viewer.mjs');
  }

  return pdfViewerModulePromise;
}

function createPageShell(pageNumber: number, scale: number, userUnit = 1) {
  const wrapper = document.createElement('section');
  wrapper.className = 'mx-auto mb-6 w-full max-w-[980px] rounded-md border border-slate-100 bg-white p-4';

  const label = document.createElement('div');
  label.className = 'mb-3 text-[11px] uppercase tracking-[0.18em] text-slate-400';
  label.textContent = `Page ${pageNumber}`;

  const viewportBox = document.createElement('div');
  viewportBox.className = 'pdf-page pdf-text-layer-host relative mx-auto overflow-hidden bg-white';
  viewportBox.style.setProperty('--scale-factor', String(scale));
  viewportBox.style.setProperty('--user-unit', String(userUnit));

  const canvas = document.createElement('canvas');
  canvas.className = 'block w-full h-auto';

  viewportBox.append(canvas);
  wrapper.append(label, viewportBox);

  return { wrapper, viewportBox, canvas };
}

async function renderTextLayer(
  page: pdfjsLib.PDFPageProxy,
  viewport: pdfjsLib.PageViewport,
  viewportBox: HTMLDivElement,
  pageNumber: number
) {
  const { TextLayerBuilder } = await loadPdfViewerModule();
  const builder = new TextLayerBuilder({ pdfPage: page });
  builder.div.dataset.pageNumber = String(pageNumber);
  viewportBox.append(builder.div);
  await builder.render({ viewport });
}

export async function renderPdfDocument(container: HTMLElement, url: string) {
  container.innerHTML = `
    <div class="flex min-h-[72vh] items-center justify-center px-6 text-center">
      <div>
        <p class="text-[11px] uppercase tracking-[0.22em] text-slate-400">Loading PDF</p>
        <p class="mt-3 text-sm leading-7 text-slate-500">Rendering pages, please wait...</p>
      </div>
    </div>
  `;

  const renderToken = `${Date.now()}-${Math.random()}`;
  container.dataset.renderToken = renderToken;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`PDF request failed: ${response.status}`);
  }

  const data = await response.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data }).promise;

  if (container.dataset.renderToken !== renderToken) {
    return { pageCount: pdf.numPages };
  }

  container.innerHTML = '';
  container.classList.add('px-4', 'py-5');

  const maxWidth = Math.max(container.clientWidth - 32, 320);

  for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber++) {
    if (container.dataset.renderToken !== renderToken) {
      return { pageCount: pdf.numPages };
    }

    const page = await pdf.getPage(pageNumber);
    const initialViewport = page.getViewport({ scale: 1 });
    const scale = Math.max(Math.min(maxWidth / initialViewport.width, 2.2), 0.8);
    const viewport = page.getViewport({ scale });

    const { wrapper, viewportBox, canvas } = createPageShell(
      pageNumber,
      scale,
      (page as pdfjsLib.PDFPageProxy & { userUnit?: number }).userUnit ?? 1
    );
    const context = canvas.getContext('2d');
    if (!context) {
      continue;
    }

    const outputScale = window.devicePixelRatio || 1;
    canvas.width = Math.floor(viewport.width * outputScale);
    canvas.height = Math.floor(viewport.height * outputScale);
    canvas.style.width = `${viewport.width}px`;
    canvas.style.height = `${viewport.height}px`;
    viewportBox.style.width = `${viewport.width}px`;
    viewportBox.style.height = `${viewport.height}px`;

    context.setTransform(outputScale, 0, 0, outputScale, 0, 0);
    container.appendChild(wrapper);

    await page.render({
      canvasContext: context,
      viewport,
    }).promise;

    await renderTextLayer(page, viewport, viewportBox, pageNumber);
  }

  return { pageCount: pdf.numPages };
}
