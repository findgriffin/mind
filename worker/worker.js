/**
 * @param {string} USERNAME User name to access the page
 * @param {string} PASSWORD Password to access the page
 * @param {string} REALM A name of an area (a page or a group of pages) to protect.
 * Some browsers may show "Enter user name and password to access REALM"
 */

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

async function hasAuthCookie(request) {
  const cookies = parseCookies(request.headers.get('Cookie') || '');
  return cookies[AUTH] != null && cookies[AUTH] == EXPECTED;
}

COOKIE_ALGO = {name: "HMAC"}

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
    console.log(`logging in ${user} ${password}`);
    if (user in LOGIN) {
      if (LOGIN[user] == toHexString(await hashPassword(SALT, password))) {
        return generateCookie(KEY)
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

async function handleLogin(request) {
  const body_json = await request.json();

  if (request.headers.get('Content-Type') == 'application/json' && body_json) {
    const cookie = await loginUser(body_json);
    console.log(cookie)
  } else {
    console.log('bad content');
    return false;
  }
}

async function handleRequest(request) {
  if (request.headers.has('authorization')) {
    const authorization = request.headers.get('authorization')
    console.log(`checking ${authorization}`)
    const creds = parseCredentials(authorization)
     if (creds[0] in USERS && users[creds[0]] == creds[1]) {
       let resp = new Response('Logged in!');
       resp.headers.set('Set-Cookie', `${AUTH}=${EXPECTED}; Secure; HttpOnly`)
       return await fetch(BASE)
     } else {
       return await fetch(BASE + 'login?result=False')
     }

  } else {
    return await fetch(BASE + 'login')
  }
}

/**
 * Break down base64 encoded authorization string into plain-text username and password
 * @param {string} authorization
 * @returns {string[]}
 */
function parseCredentials(authorization) {
  const parts = authorization.split(' ')
  const plainAuth = atob(parts[1])
  const credentials = plainAuth.split(':')
  return credentials
}

/**
 * Helper funtion to generate Response object
 * @param {string} message
 * @returns {Response}
 */
function getUnauthorizedResponse(message) {
  let response = new Response(message, {
    status: 401,
  })
  response.headers.set('WWW-Authenticate', `Basic realm="${REALM}"`)
  return response
}

addEventListener('fetch', (event) => {
  event.respondWith(handleRequest(event.request))
})
