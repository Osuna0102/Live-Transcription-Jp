// kuroshiro-module.js
import Kuroshiro from "kuroshiro";
import KuromojiAnalyzer from "kuroshiro-analyzer-kuromoji";

const kuroshiro = new Kuroshiro();

const initializeKuroshiro = async () => {
  await kuroshiro.init(new KuromojiAnalyzer());
};

export { kuroshiro, initializeKuroshiro };
