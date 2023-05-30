mouseDown = false
matChoice = "waterChoice"

function getKey(object, value) {
    return Object.keys(object).find(key => object[key] === value);
}

document.addEventListener('mousedown', function() { mouseDown = true }, true)
document.addEventListener('mouseup', function() { mouseDown = false }, true)

function setMatChoice(event) {
    matChoice = event.currentTarget.getAttribute('id')
}


var colorDict = {
    air: 'lightblue',
    fuel: "gray",
    water: "blue",
    poison: "violet"
}


function onClickCell() {
    var ID = this.getAttribute('id')
        // selected_boxes.push(ID)
        //alert(colorDict[matChoice])
    this.style.backgroundColor = colorDict[matChoice]
}

function onEnterCell() {
    if (mouseDown == true) {
        this.style.backgroundColor = colorDict[matChoice]
    }
}


const matButtons = document.querySelectorAll('.matChoice')
for (const matButton of matButtons) {
    matButton.addEventListener('click', setMatChoice, true)
    matButton.style.backgroundColor = colorDict[matButton.id]
}



// Loop through cells and add listeners
var cells = document.querySelectorAll('.cell')

for (const cell of cells) {
    cell.addEventListener('mousedown', onClickCell, true)
    cell.addEventListener('mouseenter', onEnterCell, true)
    cell.style.backgroundColor = colorDict['fuel']
}

const clearButton = document.querySelector("#clearGrid")
clearButton.addEventListener('click', clearGrid, true)

function clearGrid() {
    for (const cell of cells) {
        cell.style.backgroundColor = colorDict['fuel']
    }
}

const solveButton = document.querySelector('#solve')
solveButton.addEventListener('click', getGeo)

function getGeo() {

    geoObj = {}
    for (cell of document.querySelectorAll(".cell")) {
        geoObj[cell.id] = getKey(colorDict, cell.style.backgroundColor)
            // console.log(cell.id)
            // console.log(getKey(colorDict, cell.style.backgroundColor))
    }

    solve(geoObj)
}


function solve(geoObj) {

    $('#ajaxProgressModal').modal('show')
    
    console.log(geoObj)
    $.ajax({
        type: 'POST',
        url: 'solve/',
        // dataType: "json",
        async: true,
        data: {
            csrfmiddlewaretoken: document.querySelector('[name="csrfmiddlewaretoken"]').value,
            contentType: "application/json",
            data: JSON.stringify(geoObj),
            // complete: callback
        },
        success: function(imgContainerHtml){
            
            document.querySelector('#solutionModal').innerHTML = imgContainerHtml
            $('#solutionModal').modal('show')
            $('#ajaxProgressModal').modal('hide')
            
            
        }

    })
}