AUTH = 'Authorization'
COOKIE_ALGO = {name: "HMAC"}
PAGE = "https://mind-2ov.pages.dev";

if (typeof(USERS) == 'string') {
  USERS = JSON.parse(USERS)
}

if (typeof(LOGIN) == 'string') {
  LOGIN = JSON.parse(LOGIN)
}
HMAC = {name: "HMAC", hash: {name: "SHA-256"}};

async function importKey() {
  return await crypto.subtle.importKey("jwk", JSON.parse(SIGNING), HMAC, "true", ["sign", "verify"])
}

function toHexString(byteArray) {
  return Array.prototype.map.call(byteArray, function(byte) {
    return ('0' + (byte & 0xFF).toString(16)).slice(-2);
  }).join('');
}
const toHexAlt = (bytes) =>
    bytes.reduce((str, byte) => str + byte.toString(16).padStart(2, '0'), '');

function toByteArray(hexString) {
  var result = [];
  for (var i = 0; i < hexString.length; i += 2) {
    result.push(parseInt(hexString.substr(i, 2), 16));
  }
  return result;
}

function parseCookies(cookie_str) {
  decode = decodeURIComponent
  return cookie_str.split(';').map(c=>c.split('=')).reduce(
      (obj, cook) => {obj[decode(cook[0]).trim()] = decode(cook[1]).trim(); return obj
      }, {});
}

async function hashPassword(salt, password) {
  const myDigest = await crypto.subtle.digest(
      {name: 'SHA-256'}, new TextEncoder().encode(salt + password)
  );
  return new Uint8Array(myDigest);
}

async function validateToken(token) {
  const parts = token.split('.');
  if (parts.length == 2) {
    const data = new Uint8Array(toByteArray(parts[0]));
    const signature = new Uint8Array(toByteArray(parts[1]));
    const key = await importKey();
    return await crypto.subtle.verify(COOKIE_ALGO, key, signature, data);
  } else {
    return false;
  }
}

async function isAuthorized(request) {
  const hdrs = request.headers;
  const cookies = parseCookies(hdrs.get('Cookie') || '');
  console.log(`Cookies recieved: ${JSON.stringify(cookies)}`);
  console.log(`${AUTH} cookie: ${cookies[AUTH]}`);
  if (AUTH in cookies) {
    return validateToken(cookies[AUTH])
  } else {
    const auth = (hdrs.get(AUTH) || '').split('=');
    if (auth.length == 2) {
      return validateToken(auth[1])
    } else {
      console.warn(`bad auth header: ${auth}`)
    }
  }
}


async function generateCookie(importedKey) {
  const data = new Uint8Array(32);
  crypto.getRandomValues(data);
  const sig = await crypto.subtle.sign(COOKIE_ALGO, importedKey, data);
  const part2 = new Uint8Array(sig);
  return `${toHexAlt(data)}.${toHexAlt(part2)}`;
}

async function loginUser(user, password) {
  if (user && password) {
    if (user in LOGIN) {
      if (LOGIN[user] == toHexString(await hashPassword(SALT, password))) {
        key = await importKey();
        console.log(`SIGNING: ${SIGNING} key ${key}`)
        return await generateCookie(key)
      } else {
        console.log('bad password');
      }
    } else {
      console.log('no such user');
    }
  } else {
    console.log('missing user or password');
  }
  return false;
}

function getNotFoundResponse() {
  return new Response("Not found!", {status: 404});
}

function getUnauthorizedResponse() {
  return new Response("Unauthorized", {status: 401});
}

async function handleLogin(request) {
  const content_type = request.headers.get('Content-Type');
  let user = null; let password = null;
  if (content_type == 'application/json') {
    data = await request.json()
    user = data['user'];
    password = data['password'];
  } else {
    const formData = await request.formData();
    user = formData.get('user');
    password = formData.get('password');
  }
  const cookie = await loginUser(user, password);
  // TODO path=/; domain=[DOMAIN]; secure;
  // https://www.mikestreety.co.uk/blog/using-cloudflare-workers-to-set-a-cookie-based-on-a-get-parameter-or-path/
  if (cookie) {
    const resp = await fetch(PAGE);

    // Clone the response so that it's no longer immutable
    const newResp = new Response(resp.body, resp);
    const auth_cookie = `${AUTH}=${cookie}`
    newResp.headers.set('Set-Cookie', `${auth_cookie}; Secure; HttpOnly`);
    newResp.headers.append('AuthCookie', auth_cookie);
    return newResp;
  } else {
    return getUnauthorizedResponse();
  }
}


async function handleRequest(request) {
  if (request.method == 'POST') {
    if (request.url.endsWith('/login')) {
      return await handleLogin(request)
    } else {
      return getNotFoundResponse();
    }
  } else if (request.method == 'GET') {
    if (await isAuthorized(request)) {
      return await fetch(PAGE);
    } else {
      return await fetch(PAGE + '/login');
    }
  }
}

addEventListener('fetch', (event) => {
  event.respondWith(handleRequest(event.request))
})
