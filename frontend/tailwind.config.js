
module.exports = {
    content: [
        "./src/**/*.js",
        // This is mapped in compose.yml to the entire django/ folder
        "/django/**/*.jinja",
    ],
    theme: {
        extend: {
            colors: {
                'tone1': '#fa0000',
                'tone2': '#07b827',
                'tone3': '#4403e3',
                'tone4': '#8d09ac',
                'tone5': '#6d6d6d',
                'orange-25': '#fffaf5',
            },
        },
    },
    plugins: [
        require('@tailwindcss/forms'),
    ],
}
