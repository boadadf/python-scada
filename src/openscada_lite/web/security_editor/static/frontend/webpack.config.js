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
    clean: true
  },
  mode: isProd ? "production" : "development",

  module: {
    rules: [
      {
        test: /\.(js|jsx|ts|tsx)$/,
        exclude: (modulePath) =>
          /node_modules/.test(modulePath) && !/node_modules[\\/](login)/.test(modulePath),
        use: {
          loader: "babel-loader",
          options: {
            presets: ["@babel/preset-env", "@babel/preset-react", "@babel/preset-typescript"],
          },
        },
      },
      {
        test: /\.css$/,
        use: ["style-loader", "css-loader"],
      },
    ],
  },

  resolve: {
    extensions: [".js", ".jsx", ".ts", ".tsx"],
    alias: {
      react: path.resolve(__dirname, "node_modules/react"),
      "react-dom": path.resolve(__dirname, "node_modules/react-dom"),
      login: path.resolve(__dirname, "../../../login/src"),
      generatedApi: path.resolve(__dirname, "../../../lib/openApi"),
      liveFeed: path.resolve(__dirname, "../../../lib/liveFeed.js")
    },
  },

  plugins: [
    new HtmlWebpackPlugin({
      template: "./src/index.html",    // YOUR SPA HTML
      filename: "index.html",
    }),
    // Uncomment if you want to analyze your bundles
    // new BundleAnalyzerPlugin(),
  ],

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
    runtimeChunk: "single",
  },

  devServer: {
    static: {
      directory: path.resolve(__dirname, "dist"),
    },
    port: 3000,
    hot: true,
    historyApiFallback: true,
  },
};
