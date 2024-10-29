const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");

module.exports = (env) => {

  let entries = {
    'style': {
      import: './src/input.css',
      filename: 'deleteme.css'
    }
  }
  for (const s of [
    'reader',
  ]) {
    entries[s] = {
      import: `./src/${s}/entry.js`,
      filename: env.prod ? '[name].[contenthash].prod.js' : '[name].dev.js',
    }
  }
  return {
    entry: entries,
    devtool: 'source-map',
    output: {
      path: env.prod ? path.join(__dirname, "/dist/prod") : path.join(__dirname, "/dist/dev"),
      clean: true
    },
    module: {
      rules: [
        {
          test: /\.(js|jsx)$/,
          exclude: /node_modules/,
          use: {
            loader: "babel-loader"
          }
        },
        {
          test: /\.css$/,
          use: [
            MiniCssExtractPlugin.loader,
            'css-loader',
            'postcss-loader'
          ]
        },
        {
          test: /\.svg$/,
          use: ['@svgr/webpack'],
        },
      ]
    },
    plugins: [
      new CleanWebpackPlugin(),
      new MiniCssExtractPlugin({
        filename: env.prod ? '[name].[contenthash].css' : '[name].dev.css',
      }),
    ]
  };
}
