/** Serve the static guide under https://langcode.app/shenzhen/ */
const PREFIX = '/shenzhen';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === PREFIX) {
      return Response.redirect(`${url.origin}${PREFIX}/${url.search}`, 308);
    }

    // Collapse /shenzhen/index.html → /shenzhen/ for a single canonical home URL.
    if (url.pathname === `${PREFIX}/index.html`) {
      return Response.redirect(`${url.origin}${PREFIX}/${url.search}`, 308);
    }

    let pathname = url.pathname;
    if (pathname.startsWith(`${PREFIX}/`)) {
      pathname = pathname.slice(PREFIX.length) || '/';
    } else if (pathname === PREFIX) {
      pathname = '/';
    } else {
      return new Response('Not Found', { status: 404 });
    }

    if (pathname.endsWith('/')) {
      pathname += 'index.html';
    }

    const assetRequest = new Request(
      new URL(pathname + url.search, 'https://assets.local'),
      request,
    );
    const response = await env.ASSETS.fetch(assetRequest);

    if (response.status === 404 && !pathname.includes('.')) {
      const htmlRequest = new Request(
        new URL(`${pathname.replace(/\/$/, '')}.html${url.search}`, 'https://assets.local'),
        request,
      );
      const htmlResponse = await env.ASSETS.fetch(htmlRequest);
      if (htmlResponse.ok) return htmlResponse;
    }

    return response;
  },
};
