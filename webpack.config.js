const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = {
    entry: {
        app: './static/ts/graph-explorer.ts',
        styles: './static/scss/main.scss'
    },
    output: {
        filename: 'js/[name].bundle.js',
        path: path.resolve(__dirname, 'static/dist')
    },
    resolve: {
        extensions: ['.ts', '.js', '.scss']
    },
    module: {
        rules: [
            {
                test: /\.ts$/,
                use: 'ts-loader',
                exclude: /node_modules/
            },
            {
                test: /\.scss$/,
                use: [
                    MiniCssExtractPlugin.loader,
                    'css-loader',
                    'sass-loader'
                ]
            }
        ]
    },
    plugins: [
        new MiniCssExtractPlugin({
            filename: 'css/[name].css'
        })
    ],
    externals: {
        d3: 'd3'
    }
};