import React from 'react'
import ReaderOptions from "./ReaderOptions";
import WordInfo from "./WordInfo";
import CharacterInfo from "./CharacterInfo";
import PhraseInfo from "./PhraseInfo";
import GPTChat from "./GPTChat";

class Sidebar extends React.Component {

    render() {

        return (


          <div className="sticky top-0 h-screen overflow-y-auto">

            <div className="border-b border-zinc-200 pt-4">
              <ReaderOptions
                options={this.props.options}
                setShowPinyin={this.props.setShowPinyin}
                setShowToneColors={this.props.setShowToneColors}
              />
            </div>

            <div className="pt-2">


              {
                this.props.obj ?
                  <div>
                    {!this.props.isFrozen && (
                      <p className="text-xs mt-1 mb-2 text-zinc-400">(Click to freeze)</p>
                    )}
                    {this.props.type === 'word' && (
                      <>
                        <WordInfo obj={this.props.obj}/>
                        {this.props.cps && this.props.cps.length > 0 && (
                          <div>
                            {
                              this.props.cps.map((cp, i) => {
                                return <CharacterInfo key={i} cp={cp}/>
                              })
                            }
                          </div>

                        )}

                      </>
                    )}

                    {this.props.type === 'cp' && (
                      <WordInfo obj={this.props.obj}/>
                    )}

                    {this.props.type === 'phrase' && (
                      <div className="">
                        <PhraseInfo
                          obj={this.props.obj}
                        />
                      </div>
                    )}

                    <GPTChat
                      key={this.props.chatIdentifier}
                      articlePk={this.props.articlePk}
                      obj={this.props.type === 'phrase' ? null : this.props.obj}
                      phraseObj={this.props.phraseObj}
                      conversation={this.props.conversation}
                      addChatMessage={this.props.addChatMessage}
                      chatIdentifier={this.props.chatIdentifier}
                      isMobile={false}
                    />

                  </div> :
                  <div className="mt-2">
                    <p className="text-zinc-700">
                      Hover over a word or under a sentence for more options.
                    </p>
                  </div>
              }


            </div>

          </div>
        )
    }
}

export default Sidebar


