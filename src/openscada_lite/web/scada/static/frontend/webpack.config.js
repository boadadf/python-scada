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
        test: /\.(js|jsx|ts|tsx)$/,
        exclude: (modulePath) =>
          /node_modules/.test(modulePath) && !/node_modules[\\/](login)/.test(modulePath),
        use: {
          loader: "babel-loader",
          options: {
            presets: [
              "@babel/preset-env",
              "@babel/preset-react",
              "@babel/preset-typescript",
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

  resolve: {
    extensions: [".js", ".jsx", ".ts", ".tsx"],
    symlinks: true,
    alias: {
      react: path.resolve(__dirname, "node_modules/react"),
      "react-dom": path.resolve(__dirname, "node_modules/react-dom"),
      login: path.resolve(__dirname, "../../../login/src"),
      generatedApi: path.resolve(__dirname, "../../../lib/openApi"),
      liveFeed: path.resolve(__dirname, "../../../lib/liveFeed.js")
    },
  },

  optimization: {
    runtimeChunk: 'single',
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        reactVendor: {
          test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
          name: 'react-vendor',
          chunks: 'all',
          priority: 20,
        },
        gsapVendor: {
          test: /[\\/]node_modules[\\/]gsap[\\/]/,
          name: 'gsap-vendor',
          chunks: 'all',
          priority: 15,
        },
        leafletVendor: {
          test: /[\\/]node_modules[\\/]leaflet[\\/]/,
          name: 'leaflet-vendor',
          chunks: 'all',
          priority: 10,
        },
        vendors: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
          priority: 5,
        },
      },
    },
  },

  plugins: [
    new HtmlWebpackPlugin({
      template: "./src/index.html", // <-- your HTML template in src
      inject: "body", // inject scripts at the bottom
    }),
    // Optionally include BundleAnalyzerPlugin if you want
    // new BundleAnalyzerPlugin(),
  ],

  devServer: {
    static: path.join(__dirname, "dist"),
    port: 3000,
    hot: true,
  },
};
