API = '/'

async function getTag(tag) {
    const resp = await fetch(API, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({'query': {'tag': tag}})
    })
    return resp.json();
}

async function doStuff(operation, id, body) {
    console.log(`Doing ${operation} for ${id}`)
    await fetch(API, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({[operation]: {'id': id, 'body': body}})
    })
}

async function addStuff(tag, body) {
    console.log(`For ${tag}, adding ${body}`)
    const resp = await fetch(API, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({'add': [body, `#${tag}`]})
    });
    const resp_json = await resp.json()
    console.log(resp_json)
    return resp_json
}

function buildItem(id, tagName, record) {
    const template = document.getElementById('item');
    const clone = template.content.cloneNode(true);
    const input = clone.querySelectorAll('input')[0]
    const label = clone.querySelectorAll('label')[0]
    input.id = `${id}-${tagName}-input`
    input.onchange = async (e) =>  {
        await doStuff(input.checked ? 'tick' : 'untick', record[0], record[1])
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
    const add = clone.querySelectorAll('input')[0]
    const add_btn = clone.querySelectorAll('button')[0]
    add.id = `add-${tagName}`
    add_btn.id = `add-${tagName}-btn`
    add_btn.onclick = async (e) =>  {
        console.log(await addStuff(tagName, add.value))
        // ol.appendChild(add.value)
        console.log(`add_btn onclick for ${tagName} is ${add.value}`)
        add.value = ''
    }
    clone.querySelectorAll('h4')[0].textContent = `#${tagName}`
    document.getElementById('body').appendChild(clone);
    for (const [i, item] of items.entries()) {
        ol.appendChild(buildItem(i, tagName, item))
    }
}

window.onload = async (event) => {
    await addArticle('todo');
    await addArticle('groceries');
};
