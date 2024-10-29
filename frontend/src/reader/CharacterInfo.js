import React from 'react';
import ToneColoredString from "./ToneColoredString";

const CharacterInfo = ({cp}) => {

  if (!cp || typeof cp !== 'object') {
    console.log("Tried to render CharacterInfo with bad cp:")
    console.log(cp)
    return null;
  }
  const { url, chinese, tone, pinyin } = cp;
  if (!url || !chinese || !tone || !pinyin) {
    console.log("Tried to render CharacterInfo with bad cp:")
    console.log(cp)
    return null;
  }

  return (

        <div className="mt-3 md:mt-4">
          <h4 className="text-lg flex justify-between items-center text-zinc-400">
            <a className="font-bold" href={cp.url} target="_blank">
              <ToneColoredString chars={cp.chinese} tones={[cp.tone]} colorBehavior={false}/> {cp.pinyin}
            </a>
            <div className="text-sm text-zinc-400">
              {
                cp.freqRank &&
                <span className="">#{cp.freqRank}</span>
              }
              {
                cp.hskLevel &&
                <span
                  className="ml-1 bg-zinc-100 text-zinc-800 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium whitespace-nowrap">HSK{cp.hskLevel}</span>
              }
            </div>
          </h4>

          <ol className="list-decimal list-inside text-zinc-400 text-sm mt-1">
            {
              cp.definitions.map((definition, j) => (
                <li key={j} className="">{definition}</li>
              ))
            }
          </ol>
        </div>
  )

}

export default CharacterInfo