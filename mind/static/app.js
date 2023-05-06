STUFF = '/stuff'
TAGS = '/tags'

COUNTERS = {}

async function apiCall(path, query) {
    return (await fetch(path, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(query)
    })).json()
}

function buildItem(tagName, record) {
    id = COUNTERS[tagName]
    const template = document.getElementById('item');
    const clone = template.content.cloneNode(true);
    const input = clone.querySelectorAll('input')[0]
    const label = clone.querySelectorAll('label')[0]
    input.id = `${id}-${tagName}-input`
    input.onchange = async (e) =>  {
        operation = input.checked ? 'tick' : 'untick'
        await apiCall(STUFF, {[operation]: {'id': record[0], 'body': record[1]}})
    }
    label.appendChild(document.createTextNode(record[1]));
    label.id = `${id}-${tagName}-label`
    label.setAttribute('data-content', record[1]);
    label.setAttribute('for', `${id}-input`);
    COUNTERS[tagName]++;
    return clone
}

function addTagLink(tag) {
    const latest_list = document.getElementById('latest-tags')
    const link = document.createElement('a')
    link.href = tag ? `/tags/${tag}` : '/tags'
    link.className = 'navlink';
    link.appendChild(document.createTextNode(tag ? `#${tag}` : '[all]'))
    latest_list.appendChild(link)
}


async function addArticle(tagName) {
    const items = await apiCall(STUFF, {'query': {'tag': tagName}});
    const template = document.getElementById('article');
    const clone = template.content.cloneNode(true);
    const ol = clone.querySelectorAll('ol')[0];
    ol.id = `stuff-${tagName}`
    const add = clone.querySelectorAll('input')[0];
    const add_btn = clone.querySelectorAll('button')[0];
    add.id = `add-${tagName}`;
    add_btn.id = `add-${tagName}-btn`;
    add_btn.appendChild(document.createTextNode(`add to #${tagName}`))
    add_btn.onclick = async (e) =>  {
        const added = await apiCall(
            STUFF, {'add': [add.value, `#${tagName}`]})
        tags = added.tags // In theory there could be more tags.
        ol.insertBefore(buildItem(tagName, added.stuff), ol.firstChild);
        add.value = ''
        add.focus()
    }
    clone.querySelectorAll('h4')[0].textContent = `#${tagName}`
    document.getElementById('body').appendChild(clone);
    COUNTERS[tagName] = 0
    for (const [i, item] of items.entries()) {
        ol.appendChild(buildItem(tagName, item))
    }
}

window.onload = async (event) => {
    const tags_resp = await apiCall(TAGS, {limit: 3});
    const add = document.getElementById('add-stuff-input')
    const add_btn = document.getElementById('add-stuff-btn')
    add.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            add_btn.click()
        }
    });
    add_btn.onclick = async (e) =>  {
        added = await apiCall(STUFF, {'add': [add.value]})
        tags = added.tags // In theory there could be more tags.
        add.value = ''
        add.focus()
    }
    for (const tag of tags_resp) {
        await addTagLink(tag[1])
        await addArticle(tag[1]);
    }
    await addTagLink(null);
};
