// Copied by sstack lint-pack. Folder boundaries go in `forbidden`; each `comment` is the error text, so name the fix.
/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: "no-circular",
      severity: "error",
      comment: "Circular import. Move the shared piece into a module both sides import, or invert the dependency.",
      from: {},
      // A cycle through a type-only import is erased at build time, so it can't break module loading.
      to: { circular: true, viaOnly: { dependencyTypesNot: ["type-only"] } },
    },
    // BOUNDARIES: one entry per rule the install step agreed with the user, e.g.
    // { name: "shared-not-to-app", severity: "error", comment: "shared/ can't import app/. Move the code into shared/ or pass it in as an argument.",
    //   from: { path: "^shared/" }, to: { path: "^app/" } },
  ],
  options: {
    // TS 7 has no compiler API, and dependency-cruiser's default TS parser silently skips .ts files without it. swc parses every TS version.
    parser: "swc",
    tsConfig: { fileName: "tsconfig.json" },
    tsPreCompilationDeps: true,
    doNotFollow: { path: "node_modules" },
    exclude: { path: "(^|/)(node_modules|\\.next|dist|build|coverage)/" },
    enhancedResolveOptions: { extensions: [".ts", ".tsx", ".d.ts", ".js", ".jsx", ".mjs", ".cjs"] },
  },
};
