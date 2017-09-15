function getFileIconCode(filename) {
    const ext = filename.substr(filename.lastIndexOf('.') + 1);

    switch (ext) {
        case "jpg":
        case "png":
            return "fa-picture-o";
            break;
        case "mov":
        case "avi":
            return "fa-video-camera";
            break;
        default:
            return "fa-file"
    }
}

function bytesToSize(bytes) {
    var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes == 0) return '0 Byte';
    var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
};

// Dirty
function findInMockData(filename) {
    for (var i = 0; i < mockdata1.length; i++) {
        if (mockdata1[i].name == filename) {
            return mockdata1[i];
        }
        if (mockdata1[i].children.length) {
            for (var j = 0; j < mockdata1[i].children.length; j++) {
                if (mockdata1[i].children[j].name == filename) {
                    return mockdata1[i].children[j];
                }
            }
        }
    }

    for (var i = 0; i < mockdata2.length; i++) {
        if (mockdata2[i].name == filename) {
            return mockdata2[i];
        }
        if (mockdata2[i].children.length) {
            for (var j = 0; j < mockdata2[i].children.length; j++) {
                if (mockdata2[i].children[j].name == filename) {
                    return mockdata2[i].children[j];
                }
            }
        }
    }
    return null;
}

function moveFile(filename, destination) {
    var fileToMove = null;

    // Find file to move
    for (var i = 0; i < mockdata1.length; i++) {
        if (mockdata1[i].children.length) {
            for (var j = 0; j < mockdata1[i].children.length; j++) {
                if (mockdata1[i].children[j].name == filename) {
                    fileToMove = mockdata1[i].children[j];
                }
            }
        }
    }

    // Find bucket destination
    for (var i = 0; i < mockdata2.length; i++) {
        if (mockdata2[i].name == destination) {
            // Moving file
            mockdata2[i].children.push(fileToMove);
            console.log("Moved " + filename + " to " + destination);
            return;
        }
    }
}
