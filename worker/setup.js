function randomHex(len_bytes) {
    const arr = new Uint8Array(len_bytes);
    crypto.getRandomValues(arr);
    return toHexString(arr)
}

async function saltGen() {
    let current = document.getElementById('salt');
    if (current.value) {
        console.log('Clear salt to generate a new one');
    } else {
        current.value = randomHex(32)
        SALT = current.value;
    }
    return false;
}

async function keyGen() {
    return await window.crypto.subtle.generateKey(
        {name: "HMAC", hash: {name: "SHA-256"}},
        true, ["sign", "verify"]
    );
}
