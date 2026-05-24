import tseslint from "typescript-eslint";
import prettierConfig from "eslint-config-prettier";
import prettierPlugin from "eslint-plugin-prettier";
import simpleImportSort from "eslint-plugin-simple-import-sort";
import importX from "eslint-plugin-import-x";
import unusedImports from "eslint-plugin-unused-imports";

export default tseslint.config(
  {
    ignores: ["**/dist/**", "**/node_modules/**", "**/*.config.*"],
  },
  tseslint.configs.recommendedTypeChecked,
  {
    rules: {
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-floating-promises": "error",
      "@typescript-eslint/consistent-type-imports": [
        "error",
        { prefer: "type-imports", fixStyle: "inline-type-imports" },
      ],
      "no-console": "error",
      "no-nested-ternary": "error",
      "prefer-const": "error",
      "no-var": "error",
      "no-use-before-define": "off", // TS version handles this
    },
  },
  {
    plugins: {
      "simple-import-sort": simpleImportSort,
      "import-x": importX,
      "unused-imports": unusedImports,
    },
    rules: {
      "simple-import-sort/imports": [
        "error",
        {
          groups: [["^@/", "^@?\\w", "^\\.\\/", "^\\.\\.\\/"]],
        },
      ],
      "simple-import-sort/exports": "error",
      "import-x/newline-after-import": ["error", { count: 1 }],
      "import-x/order": "off",
      "unused-imports/no-unused-imports": "error",
      "unused-imports/no-unused-vars": [
        "warn",
        {
          vars: "all",
          varsIgnorePattern: "^_",
          args: "after-used",
          argsIgnorePattern: "^_",
          caughtErrors: "none",
        },
      ],
    },
  },
  {
    files: ["**/*.test.ts", "**/*.spec.ts"],
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-unsafe-assignment": "off",
      "@typescript-eslint/no-unsafe-member-access": "off",
    },
  },
  prettierConfig,
  {
    plugins: { prettier: prettierPlugin },
    rules: {
      "prettier/prettier": ["error", { endOfLine: "auto" }],
    },
  },
);
