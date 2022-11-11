AUTH = 'Authorization'
COOKIE_ALGO = {name: "HMAC"}
// TODO: implement hex conversion https://stackoverflow.com/a/50868276/12376646

// From https://bitcoin.stackexchange.com/questions/52727/
// byte-array-to-hexadecimal-and-back-again-in-javascript
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
      (obj, cook) => {obj[decode(cook[0])] = decode(cook[1]); return obj
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
    return await crypto.subtle.verify(COOKIE_ALGO, KEY, signature, data);
  } else {
    return false;
  }
}

async function isAuthorized(request) {
  const hdrs = request.headers;
  const cookies = parseCookies(hdrs.get('Cookie') || '');
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


async function generateCookie(key) {
  const data = new Uint8Array(32);
  crypto.getRandomValues(data);
  const sig = await crypto.subtle.sign(COOKIE_ALGO, key, data);
  const part2 = new Uint8Array(sig);
  return `${toHexAlt(data)}.${toHexAlt(part2)}`;
}

async function loginUser(body_json) {
  let {user, password } = body_json;
  if (user && password) {
    if (user in LOGIN) {
      if (LOGIN[user] == toHexString(await hashPassword(SALT, password))) {
        return await generateCookie(KEY)
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
  const body_json = await request.json();
  if (request.headers.get('Content-Type') == 'application/json' && body_json) {
    const cookie = await loginUser(body_json);
    // TODO path=/; domain=[DOMAIN]; secure;
    // https://www.mikestreety.co.uk/blog/using-cloudflare-workers-to-set-a-cookie-based-on-a-get-parameter-or-path/
    if (cookie) {
      let resp = new Response('Logged in!');
      const auth_cookie = `auth=${cookie}`
      resp.headers.set('Set-Cookie', `${auth_cookie}; Secure; HttpOnly`);
      resp.headers.append('AuthCookie', auth_cookie);
      return resp;
    } else {
      return getUnauthorizedResponse();
    }
  } else {
    console.warn('bad content');
    return getUnauthorizedResponse();
  }
}


async function handleRequest(request) {
  if (request.method == 'POST') {
    if (request.url == `${BASE}/login`) {
      return await handleLogin(request)
    } else {
      return getNotFoundResponse();
    }
  } else if (request.method == 'GET') {
    if (await isAuthorized(request)) {
      return await fetch(request);
    } else {
      return getUnauthorizedResponse();
    }
  }
}

addEventListener('fetch', (event) => {
  event.respondWith(handleRequest(event.request))
})
