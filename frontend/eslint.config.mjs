import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      "eqeqeq": ["error", "always"],
      "curly": ["error", "all"],
      "no-var": "error",
      "prefer-const": ["error", { destructuring: "all" }],
      "no-duplicate-imports": "error",
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "no-empty-function": "warn",
      "no-empty": ["error", { allowEmptyCatch: true }],
      "no-implicit-coercion": "error",
      "no-magic-numbers": [
        "warn",
        {
          "ignore": [0, 1, -1, 2],
          "ignoreArrayIndexes": true,
          "enforceConst": true,
        },
      ],
      "no-param-reassign": ["error", { props: true }],
      "consistent-return": "error",
      "default-case": "error",
      "array-callback-return": "error",
      "no-unneeded-ternary": "error",
      "prefer-template": "error",
      "no-nested-ternary": "error",
      "spaced-comment": ["error", "always", { exceptions: ["-", "+"] }],
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
