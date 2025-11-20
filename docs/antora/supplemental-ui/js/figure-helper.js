function downloadData(data, filename) {
    if (data.length == 1) {
        if (data[0].content.length == 1) {
            d = data[0].content[0];
            const blob = new Blob([d.data], { type: "plain/text;charset=utf-8" });
            downloadBlob(blob, `${d.title}.${data[0].format}`);
        }
        else {
            downloadFilesAsZip(data[0].content, filename);
        }
    }
    else if (data.length > 1) {
        downloadFilesAsZip(data, filename);
    }
    else {
        alert("No data to download");
    }
}


function downloadFilesAsZip(data, zipFilename) {
    const zip = new JSZip();
    data.forEach((d) => {
        d.content.forEach((c) => {
            const filename = `${c.title}.${d.format}`;
            zip.file(filename, c.data);
        });
    });
    zip.generateAsync({ type: "blob" }).then((blob) => downloadBlob(blob, zipFilename));
}

function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function switchTab(button, tabIndex) {
    const figureContainer = button.closest('.figure-container');
    figureContainer.querySelectorAll('.subfigure-container').forEach(subfig => {
        subfig.classList.remove('active');
        subfig.classList.add('inactive');
    });
    const activeSubfig = figureContainer.querySelector(`.subfigure-container[data-subfigure='${tabIndex}']`);
    activeSubfig.classList.add('active');
    activeSubfig.classList.remove('inactive');
}
