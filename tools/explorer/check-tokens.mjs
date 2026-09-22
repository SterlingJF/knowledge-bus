import { checkTokens } from './token-audit.mjs';

const result = checkTokens();
if (result.errors.length) {
  console.error(result.errors.join('\n'));
  process.exitCode = 1;
} else
  console.log(
    `explorer tokens: ${Object.keys(result.tokens).length} tokens; ${result.consumers.length} consumers; ${result.findings.length} classified expressions.`,
  );
