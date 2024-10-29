import React from 'react'
import BlockWord from "./BlockWord";

class Block extends React.Component {


  handleMouseOver = (e) => {
    this.props.setCurrentPhrase(this.props.phrasePk, 'current');
    e.stopPropagation();
  }

  render() {

    const pinyinStr = this.props.obj
      ? (this.props.obj.type === 'word' ? this.props.obj.pinyin.join('') : this.props.obj.pinyin)
      : null;

    return (

      <span
        className={`inline-block mt-2.5 ${this.props.readerIsFrozen ? "cursor-default" : "cursor-pointer"}`}
        onMouseOver={this.props.isMobile ? null : this.handleMouseOver}
      >
        {
          this.props.showPinyin &&
          <span className="block py-1 px-0.5 text-sm font-sans font-normal text-zinc-500">{pinyinStr}</span>
        }
        {
          this.props.obj
          ? <BlockWord
              isMobile={this.props.isMobile}
              isFrozen={this.props.frozen === 'word'}
              cid={this.props.cid}
              obj={this.props.obj}
              readerIsFrozen={this.props.readerIsFrozen}
              showToneColors={this.props.showToneColors}
              setActiveItem={this.props.setActiveItem}
              setReaderIsFrozen={this.props.setReaderIsFrozen}

              // Only required for mobile, since BlockWord is responsible for setting phrase status on mobile
              phrasePk={this.props.phrasePk}
              setCurrentPhrase={this.props.setCurrentPhrase}
            />
            : <span className={`block border border-transparent ${this.props.isMobile ? "border-b-[2px]" : ""}`}>{this.props.plainText}</span>
        }

      </span>
    )



  }
}

export default Block


