import React from 'react';
import ToneColoredString from "./ToneColoredString";

const WordInfo = ({obj}) => {

  if (!obj || typeof obj !== 'object') {
    console.log("Tried to render WordInfo with bad obj:")
    console.log(obj)
    return null;
  }
  const { url, chinese, definitions, hskLevel, freqRank, isVerified } = obj;
  if (!url || !chinese || !definitions) {
    console.log("Tried to render WordInfo with bad obj:")
    console.log(obj)
    return null;
  }

  const tones = 'tone' in obj ? [obj['tone']] : obj['tones']
  const pinyin = typeof obj['pinyin'] === 'string' ? [obj['pinyin']] : obj['pinyin']

  return (
    <div className="word-info">
      <div className="word-info-header flex justify-between items-center">
        <h3 className="text-xl font-bold">
          <a className="default-style" href={url} target="_blank">
            <ToneColoredString chars={chinese} tones={tones}/> {pinyin}
          </a>
        </h3>
        <div className="word-levels text-sm text-zinc-400">
          {
            chinese.length === 1 && freqRank &&
            <span className="freq-rank">#{freqRank}</span>
          }
          {
            !isVerified && <span>*</span>
          }
          {
            hskLevel &&
            <span
              className="ml-1 bg-zinc-100 text-zinc-800 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium whitespace-nowrap">HSK{hskLevel}</span>

          }
        </div>
      </div>
      <ol className="list-decimal list-inside text-zinc-700 text-sm mt-1">
        {
          definitions.map((definition, i) => (
            <li key={i} className="">{definition}</li>
          ))
        }
      </ol>
    </div>

  )

}


export default WordInfo