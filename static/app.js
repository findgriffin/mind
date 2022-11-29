API = '/'

async function getTag(tag) {
    const resp = await fetch(API, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({'query': {'tag': tag}})
    })
    return resp.json();
}

async function doStuff(operation, id) {
    console.log(`Doing ${operation} for ${id}`)
    await fetch(API, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({[operation]: {'id': id}})
    })
}

function addItem(id, tagName, record) {
    const template = document.getElementById('item');
    const clone = template.content.cloneNode(true);
    const input = clone.querySelectorAll('input')[0]
    const label = clone.querySelectorAll('label')[0]
    input.id = `${id}-${tagName}-input`
    input.onchange = async (e) =>  {
        await doStuff(input.checked ? 'tick' : 'untick', record[0])
    }
    label.appendChild(document.createTextNode(record[1]));
    label.id = `${id}-${tagName}-label`
    label.setAttribute('data-content', record[1]);
    label.setAttribute('for', `${id}-input`);
    return clone
}

async function addArticle(tagName) {
    const items = await getTag(tagName);
    const template = document.getElementById('article');
    const clone = template.content.cloneNode(true);
    const ol = clone.querySelectorAll('ol')[0]
    clone.querySelectorAll('h4')[0].textContent = `#${tagName}`
    document.getElementById('body').appendChild(clone);
    for (const [i, item] of items.entries()) {
        ol.appendChild(addItem(i, tagName, item))
    }
}

window.onload = async (event) => {
    await addArticle('todo');
    await addArticle('groceries');
};
