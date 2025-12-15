function copyCitation(elementId) {
    const preElement = document.getElementById(elementId);
    if (!preElement) {
        console.error('Element not found:', elementId);
        return;
    }
    const text = preElement.innerText;
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text)
            .then(() => {
                alert('Citation copied to clipboard successfully!');
            })
            .catch(err => {
                console.error('Failed to copy text: ', err);
                alert('Error copying citation. Please try again.');
            });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            alert('Citation copied to clipboard!');
        } catch (err) {
            console.error('Fallback copy failed: ', err);
            alert('Copy failed. Please select and copy manually.');
        }
        document.body.removeChild(textArea);
    }
}