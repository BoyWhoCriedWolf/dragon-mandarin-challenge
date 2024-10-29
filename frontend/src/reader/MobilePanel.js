import React from 'react'
import WordInfo from "./WordInfo";
import CharacterInfo from "./CharacterInfo";

import DictionaryLogo from "../assets/translate.svg"
import SentenceLogo from "../assets/sentence.svg";
import ChatLogo from "../assets/chat.svg";
import SettingsLogo from "../assets/settings.svg";
import ReaderOptions from "./ReaderOptions";
import PhraseInfo from "./PhraseInfo";
import GPTChat from "./GPTChat";

class MobilePanel extends React.Component {

  state = {
    selectedTab: 'dictionary',
  }

  setSelectedTab = (tab) => {
    this.setState({selectedTab: tab})
  }

  renderTabs = () => {

    const tabs = [
      ['dictionary', 'Dictionary', DictionaryLogo],
      ['sentence', 'Sentence', SentenceLogo],
      ['chat', 'Chat', ChatLogo],
      ['settings', 'Settings', SettingsLogo],
    ]

    return (
      <ul className="flex w-full space-x-[8px]">
        {tabs.map(([key, label, Logo]) => (
          <li
            key={key}
            className={`py-1 px-3 flex-1 flex-grow flex flex-col items-center border rounded-md ${
              this.state.selectedTab === key
                ? "border-zinc-400 bg-zinc-400 text-white"
                : "border-zinc-300 text-zinc-400"
            }`}
            onClick={() => this.setSelectedTab(key)}
          >
            <Logo className={`w-[20px] h-auto ${this.state.selectedTab === key ? '!text-white !fill-current' : ''}`} />
            <div className="text-xs">
              {label}
            </div>
          </li>
        ))}
      </ul>
    )

  }

  renderTabContent = (tab) => {

    switch (this.state.selectedTab) {
      case 'dictionary':
        return (
          <div>
            <WordInfo obj={this.props.obj}/>
            {
              this.props.cps &&
              <div className="pt-1">
                {
                  this.props.cps.map((cp, i) => (
                    <div key={i} className="">
                      <CharacterInfo cp={cp}/>
                    </div>
                  ))
                }
              </div>
            }
          </div>
        )

      case 'sentence':
        return (
          <div>
            {
              this.props.currentPhraseObj &&
              <PhraseInfo
                obj={this.props.currentPhraseObj}
              />
            }
          </div>
        )
      case 'chat':
        return (
          // mt-auto instead of flex-end on the parent, per https://stackoverflow.com/a/37515194
          <div className="!mt-auto">
            <GPTChat
              obj={this.props.obj}
              articlePk={this.props.articlePk}
              phraseObj={this.props.phraseObj}
              conversation={this.props.conversation}
              addChatMessage={this.props.addChatMessage}
              chatIdentifier={this.props.chatIdentifier}
              isMobile={true}
            />
          </div>
        )
      case 'settings':
        return (
          <div>
            <ReaderOptions
              options={this.props.options}
              setShowPinyin={this.props.setShowPinyin}
              setShowToneColors={this.props.setShowToneColors}
            />

          </div>
        )
      default:
        return null;
    }

  }

  render() {

    return (

      <div className={`sticky top-0 w-full px-3 flex bg-white border-b border-t border-zinc-200 h-[220px] ${this.props.obj ? 'flex-col' : 'items-center content-center'}`}>

        {
          this.props.obj ?
            <>
              <div className={`flex-1 pt-3 overflow-y-auto ${this.state.selectedTab === 'chat' ? 'flex flex-col flex-nowrap' : ''}`}>
                {this.renderTabContent(this.state.selectedTab)}
              </div>
              <div className="h-[63px] flex items-center justify-center">
                {this.renderTabs()}
              </div>
            </> :
            <div className="py-3 text-zinc-400 w-full">
              <div className="text-center">
                Select a word for more options.
              </div>
            </div>
          }

        </div>

      )

  }
}

export default MobilePanel


