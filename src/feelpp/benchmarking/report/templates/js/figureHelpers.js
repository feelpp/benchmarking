function downloadFilesAsZip(data, zipFilename) {
    const zip = new JSZip();

    data.forEach((d) => {
        d.content.forEach((c) => {
        const filename = `${c.title}.${d.format}`;
        zip.file(filename, c.data);
        });
    });

    zip.generateAsync({ type: "blob" }).then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = zipFilename || "download.zip";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });
}


function switchTab(figureIndex, tabIndex) {
    let subfigures = document.querySelectorAll(`[id^="subfig_${figureIndex}_"]`);
    subfigures.forEach(subfig => {
        subfig.classList.remove('active');
        subfig.classList.add('inactive');
    });

    let activeSubfig = document.getElementById(`subfig_${figureIndex}_${tabIndex}`);
    if(activeSubfig){
        activeSubfig.classList.remove('inactive');
        activeSubfig.classList.add('active');
    }
}