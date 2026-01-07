const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const { BundleAnalyzerPlugin } = require("webpack-bundle-analyzer");

const isProd = process.env.NODE_ENV === "production";

module.exports = {
  entry: "./src/index.jsx",

  output: {
    path: path.resolve(__dirname, "dist"),
    filename: isProd ? "[name].[contenthash].js" : "[name].js",
    chunkFilename: isProd ? "[name].[contenthash].chunk.js" : "[name].chunk.js",
    clean: true,
  },

  mode: isProd ? "production" : "development",

  module: {
    rules: [
      {
        test: /\.jsx?$/,
        exclude: (modulePath) => {
          return /node_modules/.test(modulePath) && !/node_modules[\\/](login)/.test(modulePath);
        },
        use: {
          loader: "babel-loader",
          options: {
            presets: ["@babel/preset-env", "@babel/preset-react"],
          },
        },
      },
      {
        test: /\.css$/i,
        use: ["style-loader", "css-loader"],
      },
    ],
  },

  resolve: {
    extensions: [".js", ".jsx"],
    symlinks: true,
    alias: {
      react: path.resolve(__dirname, "node_modules/react"),
      "react-dom": path.resolve(__dirname, "node_modules/react-dom"),
      login: path.resolve(__dirname, "../../../login/src")
    },
  },

  optimization: {
    splitChunks: {
      chunks: "all",
      cacheGroups: {
        react: {
          test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
          name: "react",
          chunks: "all",
        },
      },
    },
    runtimeChunk: 'single', // separates webpack runtime into its own file
  },
  plugins: [
      new HtmlWebpackPlugin({
          template: './src/index.html'
      })
  ],
  devServer: {
    static: path.join(__dirname, "dist"),
    port: 3000,
    hot: true,
  },
};
