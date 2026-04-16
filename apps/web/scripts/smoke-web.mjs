const baseUrl = process.env.WEB_URL ?? "http://localhost:3000";
const routes = ["/", "/catalog", "/wallet", "/feed", "/integrate", "/connect"];

async function checkRoute(route) {
  const response = await fetch(`${baseUrl}${route}`);
  if (!response.ok) {
    throw new Error(`Route ${route} returned ${response.status}`);
  }
  const html = await response.text();
  if (!html.includes("<html")) {
    throw new Error(`Route ${route} did not return HTML`);
  }
}

async function checkFallbackHint() {
  const response = await fetch(`${baseUrl}/integrate`);
  const html = await response.text();
  if (!html.includes("Resilient mode")) {
    throw new Error("Expected resilient fallback hint on /integrate");
  }
}

async function main() {
  const failures = [];

  for (const route of routes) {
    try {
      await checkRoute(route);
      console.log(`PASS route: ${route}`);
    } catch (error) {
      failures.push(`FAIL route: ${route} (${error.message})`);
    }
  }

  try {
    await checkFallbackHint();
    console.log("PASS fallback: /integrate includes resilient fallback hint");
  } catch (error) {
    failures.push(`FAIL fallback: ${error.message}`);
  }

  if (failures.length) {
    for (const failure of failures) {
      console.error(failure);
    }
    process.exit(1);
  }
}

main().catch((error) => {
  console.error(`Smoke failed: ${error.message}`);
  process.exit(1);
});
