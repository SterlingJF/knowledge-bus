import { fileURLToPath } from "node:url";

// Register bundled skills in memory. Never copy files or edit the user's config.
export default async function knowledgeBus() {
  const skillsPath = fileURLToPath(new URL("./skills", import.meta.url));
  return {
    async config(config) {
      config.skills ??= {};
      config.skills.paths = [...new Set([...(config.skills.paths ?? []), skillsPath])];
    },
  };
}
