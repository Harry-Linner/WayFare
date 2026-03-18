import * as pdfjsLib from 'pdfjs-dist/build/pdf.mjs';
import workerSrc from 'pdfjs-dist/build/pdf.worker.min.mjs?url';

pdfjsLib.GlobalWorkerOptions.workerSrc = workerSrc;

function createPageShell(pageNumber: number) {
  const wrapper = document.createElement('section');
  wrapper.className = 'mx-auto mb-6 w-full max-w-[980px] rounded-md border border-slate-100 bg-white p-4';

  const label = document.createElement('div');
  label.className = 'mb-3 text-[11px] uppercase tracking-[0.18em] text-slate-400';
  label.textContent = `Page ${pageNumber}`;

  const viewportBox = document.createElement('div');
  viewportBox.className = 'pdf-page relative mx-auto overflow-hidden bg-white';

  const canvas = document.createElement('canvas');
  canvas.className = 'block w-full h-auto';

  const textLayer = document.createElement('div');
  textLayer.className = 'textLayer absolute inset-0 overflow-hidden';
  textLayer.dataset.pageNumber = String(pageNumber);

  viewportBox.append(canvas, textLayer);
  wrapper.append(label, viewportBox);

  return { wrapper, viewportBox, canvas, textLayer };
}

async function renderTextLayer(
  page: pdfjsLib.PDFPageProxy,
  viewport: pdfjsLib.PageViewport,
  textLayer: HTMLDivElement
) {
  const textContent = await page.getTextContent();
  const layer = new pdfjsLib.TextLayer({
    textContentSource: textContent,
    container: textLayer,
    viewport,
  });
  await layer.render();
}

export async function renderPdfDocument(container: HTMLElement, url: string) {
  container.innerHTML = `
    <div class="flex min-h-[72vh] items-center justify-center px-6 text-center">
      <div>
        <p class="text-[11px] uppercase tracking-[0.22em] text-slate-400">Loading PDF</p>
        <p class="mt-3 text-sm leading-7 text-slate-500">正在加载并渲染文档，请稍候…</p>
      </div>
    </div>
  `;

  const renderToken = `${Date.now()}-${Math.random()}`;
  container.dataset.renderToken = renderToken;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`PDF 请求失败：${response.status}`);
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

    const { wrapper, viewportBox, canvas, textLayer } = createPageShell(pageNumber);
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

    await renderTextLayer(page, viewport, textLayer);
  }

  return { pageCount: pdf.numPages };
}
