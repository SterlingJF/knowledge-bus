import { mountUniverseViewer, type ViewerHandle } from './component-patterns/universe-viewer';
import { parseEmbedded } from './lib/embed';

type StandaloneHost = HTMLElement & { explorerViewer?: ViewerHandle };

const host = document.getElementById('explorer') as StandaloneHost | null;
const data = document.getElementById('explorer-model');
if (host && data) {
  try {
    host.explorerViewer = mountUniverseViewer(host, parseEmbedded(data.textContent ?? ''));
  } catch (error) {
    host.textContent = `This file's embedded universe model cannot be shown: ${error instanceof Error ? error.message : String(error)}`;
  }
}
