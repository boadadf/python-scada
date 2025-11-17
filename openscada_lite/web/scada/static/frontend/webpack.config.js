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
        test: /\.(js|jsx)$/,
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
    },
  },

  optimization: {
    runtimeChunk: 'single', // keeps runtime in its own small file
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        // Separate react and react-dom into their own chunk
        reactVendor: {
          test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
          name: 'react-vendor',
          chunks: 'all',
          priority: 20,
        },
        // Separate GSAP into its own chunk
        gsapVendor: {
          test: /[\\/]node_modules[\\/]gsap[\\/]/,
          name: 'gsap-vendor',
          chunks: 'all',
          priority: 15,
        },
        // Separate Leaflet into its own chunk
        leafletVendor: {
          test: /[\\/]node_modules[\\/]leaflet[\\/]/,
          name: 'leaflet-vendor',
          chunks: 'all',
          priority: 10,
        },
        // Everything else from node_modules goes into vendors
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
    ...(process.env.ANALYZE ? [new BundleAnalyzerPlugin()] : []),
  ],

  devServer: {
    static: path.join(__dirname, "dist"),
    port: 3000,
    hot: true,
  },
};
