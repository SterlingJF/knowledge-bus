import { type ExplorerModel, type GuidanceEntry } from './model';

export const guidanceKindIds = (model: ExplorerModel): string[] => (model.guidance?.kinds ?? []).map((kind) => kind.id);

export const guidanceEntries = (model: ExplorerModel): GuidanceEntry[] => model.guidance?.entries ?? [];

export const guidanceFor = (model: ExplorerModel, subject: string): GuidanceEntry[] =>
  guidanceEntries(model).filter((entry) => entry.subject === subject);

export const subjectsCarryingGuidance = (model: ExplorerModel): string[] => [
  ...new Set(guidanceEntries(model).map((entry) => entry.subject)),
];

export const subjectsTheGuidanceLeavesBare = (model: ExplorerModel, kinds: string[]): string[] => {
  const carried = new Set(subjectsCarryingGuidance(model));
  return model.entities.filter((entity) => kinds.includes(entity.kind) && !carried.has(entity.id)).map((entity) => entity.id);
};
