import React from 'react'
import Block from "./Block";
import parse, { domToReact } from 'html-react-parser';
import FeedbackForm from "./FeedbackForm";



class ReaderBody extends React.Component {

  state = {
    isScrolling: false
  }


  shouldComponentUpdate(nextProps, nextState, nextContext) {
      let res = (
        this.props.data === null ||
        nextProps.data.article.source !== this.props.data.article.source ||
        nextProps.isMobile !== this.props.isMobile ||
        nextProps.showPinyin !== this.props.showPinyin ||
        nextProps.showToneColors !== this.props.showToneColors ||

        nextProps.isFrozen !== this.props.isFrozen ||
        nextProps.currentPhrase !== this.props.currentPhrase ||
        nextProps.activeItem !== this.props.activeItem ||

        false
      );
      return res;
  }

  handleClick = (e) => {
    this.props.unfreeze();
  }

  handleTouchStart = (e) => {
    this.setState(prevState => {
      return {
        isScrolling: false
      }
    });
  }

  handleTouchMove = (e) => {
    this.setState(prevState => {
      return {
        isScrolling: true
      }
    });
  }

  handleTouchEnd = (e) => {
    if (!this.state.isScrolling) {
      this.props.unfreeze();
      this.props.setCurrentPhrase(null);
    }
  }

  handleMouseOver = (e) => {
    if (!this.props.isFrozen) {
      this.props.setCurrentPhrase(null);
      this.props.clearActiveItem();
    }
  }

  replaceNode = (node) => {

    if (node.type !== 'tag') {
      return;
    }

    let {name, attribs, children} = node;

    if (name.startsWith('d:')) {

      let props = {
        cid: attribs.cid,
        readerIsFrozen: this.props.isFrozen,
        showToneColors: this.props.showToneColors,
        showPinyin: this.props.showPinyin,
        // All of these functions become noops if isScrolling is set - that way we don't treat scrolling like a tap (affects mobile only)
        setActiveItem: ((...args) => !this.state.isScrolling && this.props.setActiveItem(...args)),
        setReaderIsFrozen: ((...args) => !this.state.isScrolling && this.props.setIsFrozen(...args)),
        setCurrentPhrase: ((...args) => !this.state.isScrolling && this.props.setCurrentPhrase(...args)),
      }

      if (name === 'd:plain') {
        props.plainText = children?.map(child => child.data).join('')

      } else if (name === 'd:cp') {
        props.obj = this.props.data.cps[attribs['obj']];

      } else if (name === 'd:word') {
        props.obj = this.props.data.words[attribs['obj']];
      }

      props.phrasePk = attribs?.phrase ?? null;
      let phraseStatus = null;
      if (props.phrasePk === this.props.currentPhrase) {
        if (!this.props.isMobile && this.props.activeItem && this.props.activeItem.type === 'phrase' && this.props.activeItem.pk === props.phrasePk) {
          if (this.props.isFrozen) {
            phraseStatus = 'frozen';
          } else {
            phraseStatus = 'hover';
          }
        } else {
          phraseStatus = 'current'
        }
      }
      props.phraseStatus = phraseStatus;

      let frozen = null;
      if (this.props.isFrozen && this.props.activeItem) {
        if (['word', 'cp'].includes(this.props.activeItem.type) && this.props.activeItem.cid === props.cid) {
          frozen = 'word';
        } else if (this.props.activeItem.type === 'phrase' && this.props.activeItem.pk === props.phrasePk) {
          frozen = 'phrase';
        }
      }
      props.frozen = frozen;

      return <Block key={props.cid} isMobile={this.props.isMobile} {...props}/>
    }


  };


  render() {

    if (this.props.data === null) {
      return <div className="text-muted text-zinc-500 mb-4 p-3"><p>Loading...</p></div>
    }

    return (
      <div>

        <div
          className="reader-body font-light bg-orange-25 md:bg-white px-3 pt-3 md:pt-1"
          onTouchStart={this.props.isMobile ? this.handleTouchStart : null}
          onTouchMove={this.props.isMobile ? this.handleTouchMove : null}
          onTouchEnd={this.props.isMobile ? this.handleTouchEnd : null}
          onClick={this.props.isMobile ? null : this.handleClick}
          onMouseOver={this.handleMouseOver}
        >

          {

            parse(this.props.data.article.source, {replace: this.replaceNode})
          }

        </div>

        <FeedbackForm />




      </div>
    )

  }
}

export default ReaderBody


