const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const isProd = process.env.NODE_ENV === "production";

module.exports = {
  mode: process.env.NODE_ENV === "production" ? "production" : "development",
  entry: "./src/index.js",
  output: {
    path: path.resolve(__dirname, "dist"),
    filename: isProd ? "[name].[contenthash].js" : "[name].js",
    chunkFilename: isProd ? "[name].[contenthash].chunk.js" : "[name].chunk.js",
    clean: true,
    publicPath: "/scada/login/",
  },
  resolve: {
    extensions: [".js", ".jsx", ".ts", ".tsx"],
    symlinks: true,
    alias: {
      generatedApi: path.resolve(__dirname, "../lib/openApi")
    },
  },  
  module: {
    rules: [
      {
        test: /\.(js|jsx|ts|tsx)$/, // Add support for TypeScript files
        exclude: /node_modules/,
        use: {
          loader: "babel-loader",
          options: {
            presets: [
              "@babel/preset-env",
              "@babel/preset-react",
              "@babel/preset-typescript", // Add TypeScript support
            ],
          },
        },
      },
      {
        test: /\.css$/i,
        use: ["style-loader", "css-loader"],
      },
    ],
  },
  externals: {
    react: "react",
    "react-dom": "react-dom",
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: "./src/index.html",
      filename: "index.html",
    }),
  ],
};
