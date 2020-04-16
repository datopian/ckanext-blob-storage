const path = require('path');
const assetPath = './ckanext/external_storage/fanstatic/js';

module.exports = {
  mode: 'production',
  devtool: "source-map",
  context: path.resolve(__dirname),
	entry: {
    "index": `./node_modules/ckan3-js-sdk/lib/index.js`,
  },
	output: {
    path: path.resolve(__dirname, assetPath, 'dist'),
    filename: '[name].js',
    libraryTarget: 'var',
    library: 'ckanUploader',// The variable name to access the library
	},
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: "babel-loader"
        }
      }
    ]
  },
  node: { fs: 'empty' },
};
