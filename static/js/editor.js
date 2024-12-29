document.addEventListener('DOMContentLoaded', function() {
    const editor = document.getElementById('editor');
    const preview = document.getElementById('preview');

    if (editor && preview) {
        editor.addEventListener('input', function() {
            // Actualizar preview
            preview.innerHTML = editor.value;
            
            // Renderizar LaTeX
            if (window.MathJax) {
                MathJax.typesetPromise([preview]).catch((err) => console.log(err));
            }
        });
    }
});
