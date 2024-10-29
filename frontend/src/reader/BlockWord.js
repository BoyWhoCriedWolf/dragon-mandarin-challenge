import React from 'react'
import ToneColoredString from "./ToneColoredString";

class BlockWord extends React.Component {

  state = {
    charCycle: 0
  }

  handleMouseOver = (e) => {
    // Set this word/cp as global activeItem so it shows in the sidebar
    this.props.setActiveItem(this.props.cid, this.props.obj.type, this.props.obj.pk);
  }

  handleClick = (e) => {
    // Set as active item again, just to be safe
    this.props.setActiveItem(this.props.cid, this.props.obj.type, this.props.obj.pk);
    // Toggle reader global frozen state
    this.props.setReaderIsFrozen(!this.props.readerIsFrozen);

    // This is usually set by Block on mouseover, but it's also occasionally possible to freeze a phrase without
    // triggering mouseover first, so we set it again here to be safe
    this.props.setCurrentPhrase(this.props.phrasePk, 'current');
    e.stopPropagation()

  }

  handleTouchEnd = (e) => {

    if (this.props.isFrozen) {
      this.setState(prevState => ({
        charCycle: prevState.charCycle + 1
      }));
    }


    this.props.setActiveItem(this.props.cid, this.props.obj.type, this.props.obj.pk);
    // On desktop, this happens in the parent Block component. On mobile, it's cleaner if it happens iff the user
    // selects a word, so we put it here.
    this.props.setCurrentPhrase(this.props.phrasePk, 'current');
    this.props.setReaderIsFrozen(true);
    e.stopPropagation();

  }

  render() {

    const {type, chinese} = this.props.obj;
    const tones = type === 'word' ? this.props.obj.tones : [this.props.obj.tone]

    return (
      <span
        className={[
          "block border border-transparent",
          this.props.isMobile ? "border-b-[2px] border-b-zinc-300 ml-[2px]" : "",
          this.props.readerIsFrozen ? "" : "md:hover:border-zinc-300",
          this.props.isFrozen ? "bg-zinc-900 border border-transparent border-b-transparent text-white" : "",
        ].join(' ')}
        onTouchEnd={this.props.isMobile ? this.handleTouchEnd : null}
        onMouseOver={this.props.isMobile ? null : this.handleMouseOver}
        onClick={this.props.isMobile ? null : this.handleClick}
      >
        {
          <ToneColoredString
            chars={chinese}
            tones={tones}
            colorBehavior={
              !this.props.isFrozen &&
              (
                this.props.readerIsFrozen
                  ? this.props.showToneColors
                  : this.props.showToneColors
                    ? true
                    : this.props.isMobile ? false : 'hover'
              )
            }
          />
        }
      </span>
    )
  }
}

export default BlockWord;
