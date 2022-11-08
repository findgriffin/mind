/**
 * @param {string} USERNAME User name to access the page
 * @param {string} PASSWORD Password to access the page
 * @param {string} REALM A name of an area (a page or a group of pages) to protect.
 * Some browsers may show "Enter user name and password to access REALM"
 */

const REALM = 'Secure Area';
const BASE = 'https://mind-2ov.pages.dev/';
const AUTH = 'Authorization';
const EXPECTED = '340918340982349090874231947234';

const USERS = {
  'kk': 'bobcat',
  'davo': 'bobby',
};
/* from https://github.com/jshttp/cookie/blob/master/index.js */
function parse(str, options) {
  if (typeof str !== 'string') {
    throw new TypeError('argument str must be a string');
  }

  var obj = {}
  var opt = options || {};
  var dec = opt.decode || decode;

  var index = 0
  while (index < str.length) {
    var eqIdx = str.indexOf('=', index)

    // no more cookie pairs
    if (eqIdx === -1) {
      break
    }

    var endIdx = str.indexOf(';', index)

    if (endIdx === -1) {
      endIdx = str.length
    } else if (endIdx < eqIdx) {
      // backtrack on prior semicolon
      index = str.lastIndexOf(';', eqIdx - 1) + 1
      continue
    }

    var key = str.slice(index, eqIdx).trim()

    // only assign once
    if (undefined === obj[key]) {
      var val = str.slice(eqIdx + 1, endIdx).trim()

      // quoted values
      if (val.charCodeAt(0) === 0x22) {
        val = val.slice(1, -1)
      }

      obj[key] = tryDecode(val, dec);
    }

    index = endIdx + 1
  }

  return obj;
}

addEventListener('fetch', (event) => {
  event.respondWith(handleRequest(event.request))
})

async function hasAuthCookie(request) {
  const cookies = parse(request.headers.get('Cookie') || '');
  return cookie[AUTH] != null && cookie[AUTH] == EXPECTED;
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
