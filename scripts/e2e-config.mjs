export const REPRESENTATIVE_ROUTES = [
  { path: "/", key: "home", kind: "home" },
  { path: "/writing/", key: "writing", kind: "index" },
  { path: "/work/", key: "work", kind: "index" },
  { path: "/about/", key: "about", kind: "profile" },
  { path: "/hire/", key: "hire", kind: "profile" },
  { path: "/resume/", key: "resume", kind: "profile" },
  { path: "/writing/tags/", key: "topics", kind: "index" },
  { path: "/writing/tags/postgres/", key: "tag", kind: "index" },
  { path: "/writing/pgbackrest-tls-ansible-rhel8/", key: "post-tutorial", kind: "post" },
  { path: "/writing/failover-lab-six-engines-eight-scenarios/", key: "post-table", kind: "post" },
  { path: "/writing/building-data-platforms-and-ai-products/", key: "post-essay", kind: "post" },
  { path: "/writing/scylladb-nodetool-refresh-upload-truncate-marker/", key: "post-series", kind: "post" },
  { path: "/work/data-platform-practice/", key: "case-practice", kind: "case" },
  { path: "/work/multi-engine-ha-lab/", key: "case-lab", kind: "case" },
  { path: "/work/clickhomes/", key: "case-product", kind: "case" },
];

export const HERO_ROUTES = REPRESENTATIVE_ROUTES.filter(({ kind }) =>
  ["home", "index", "profile", "post", "case"].includes(kind),
);

export const BREAKPOINT_PASSES = [
  { name: "phone-320-light", width: 320, height: 720, colorScheme: "light" },
  { name: "phone-390-light", width: 390, height: 844, colorScheme: "light" },
  { name: "phone-390-dark", width: 390, height: 844, colorScheme: "dark" },
  { name: "tablet-768-light", width: 768, height: 1024, colorScheme: "light" },
  { name: "nav-863-light", width: 863, height: 900, colorScheme: "light" },
  { name: "nav-864-light", width: 864, height: 900, colorScheme: "light" },
  { name: "toc-1099-light", width: 1099, height: 900, colorScheme: "light" },
  { name: "toc-1100-light", width: 1100, height: 900, colorScheme: "light" },
  { name: "laptop-1280-dark", width: 1280, height: 800, colorScheme: "dark" },
  { name: "desktop-1440-light", width: 1440, height: 900, colorScheme: "light" },
  { name: "desktop-1440-dark", width: 1440, height: 900, colorScheme: "dark" },
];

export function isPhone(pass) {
  return pass.width <= 390;
}

export function routesForPass(pass) {
  if (pass.width === 863 || pass.width === 864) {
    return REPRESENTATIVE_ROUTES.filter(({ key }) => ["home", "post-tutorial"].includes(key));
  }
  if (pass.width === 1099 || pass.width === 1100) {
    return REPRESENTATIVE_ROUTES.filter(({ key }) => key === "post-tutorial");
  }
  if (pass.colorScheme === "dark" || pass.width === 1280) {
    return REPRESENTATIVE_ROUTES.filter(({ key }) =>
      ["home", "writing", "work", "about", "post-tutorial", "case-practice"].includes(key),
    );
  }
  return REPRESENTATIVE_ROUTES;
}
