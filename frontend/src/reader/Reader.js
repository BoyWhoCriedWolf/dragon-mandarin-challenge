import React from 'react'
import Sidebar from "./Sidebar";
import ReaderBody from "./ReaderBody";
import MobilePanel from "./MobilePanel";

class Reader extends React.Component {

  state = {
    isMobile: false,
    options: {
      showPinyin: false,
      showToneColors: false,
    },
    activeItem: null, // {cid, type, pk}, cid is null if active item is a phrase

    currentPhrase: null, // null or pk

    chats: {},

    isFrozen: false,
    data: null,
    // {
    //   article: {
    //     source: null,  // (inflated html)
    //     summary: null,
    //   },
    //   words: null,
    //   cps: null,
    //   phrases: null,
    // }
  };

  websocket = null;

  updateIsMobile = () => {
    // 768 matches Tailwind md breakpoint
    this.setState({isMobile: window.innerWidth <= 768});
  }

  setShowPinyin = (val) => {
    this.setState(prevState => ({
      options: {
        ...prevState.options,
        showPinyin: val,
      }
    }));
  }

  setShowToneColors = (val) => {
    this.setState(prevState => ({
      options: {
        ...prevState.options,
        showToneColors: val,
      }
    }));
  }

  setActiveItem = (cid, type, pk) => {
    if (!this.state.isFrozen || this.state.isMobile) {
      this.setState({
        activeItem: {
          cid: cid,
          type: type,
          pk: pk,
        }
      });
    }
  }

  clearActiveItem = () => {
    this.setState({
      activeItem: null,
      isFrozen: false,
    });
  }

  setIsFrozen = (isFrozen) => {
    this.setState({
      isFrozen: isFrozen,
    });
  }

  unfreeze = () => {
    this.setState({
      isFrozen: false,
    })
  }

  setCurrentPhrase = (phrasePk) => {
    if (this.state.isMobile || !this.state.isFrozen) {
      this.setState({
        currentPhrase: phrasePk,
      })
    }
  }

  getCurrentPhraseObj = () => {
    if (this.state.currentPhrase) {
      return this.state.data.phrases[this.state.currentPhrase]
    } else {
      return null;
    }
  }

  getActiveObj = () => {
    // We only store (cid, type, pk) in this.state; this function gets the actual client_obj
    const {cid, type, pk} = this.state.activeItem;
    const obj = {
      'word': this.state.data.words,
      'cp': this.state.data.cps,
      'phrase': this.state.data.phrases,
    }[type][pk];
    return obj;
  }

  getActiveChatIdentifier = () => {
    if (!this.state.activeItem) {
      return null;
    }
    return ['cid', 'type', 'pk'].map(k => this.state.activeItem[k]).join('-');
  }

  getActiveWordCPs = () => {
    if (this.state.activeItem === null) {
      return null;
    }
    const {cid, type, pk} = this.state.activeItem;
    if (type === 'word') {
      const obj = this.getActiveObj();
      return obj['cps'].map((pk) => this.state.data.cps[pk]);
    }
    return null;
  }

  getActiveConversation = () => {
    if (!this.state.activeItem) {
      return null;
    }
    return this.state.chats[this.getActiveChatIdentifier()] ?? [];
  }

  addChatMessage = (chatIdentifier, sender, message) => {
    this.setState(prevState => {
      const newChats = { ...prevState.chats };
      const updatedChat = newChats[chatIdentifier] ? [...newChats[chatIdentifier]] : [];
      updatedChat.push({ sender, message });

      return {
        chats: {
          ...newChats,
          [chatIdentifier]: updatedChat
        }
      };
    });

  }


  fetchData = () => {

    // Open websocket to get live updates from GPT
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/articles/${this.props.articlePk}`;
    this.websocket = new WebSocket(wsUrl);
    this.websocket.onmessage = this.handleWebSocketMessage;

    fetch(`/api/v0/reader/articles/${this.props.articlePk}`)
      .then(res => res.json())
      .then((data) => {


        let words = data['words']

        this.setState({
          data: {
            article: {
              source: data['inflated'],
              summary: data['english_summary'],
            },
            words: words,
            cps: data['cps'],
            phrases: data['phrases'],
          },
        });


      })
      .catch(console.log);
  }

  handleWebSocketMessage = (event) => {
    if (!this.state.data) {
      // Fetch is not complete yet - this happens reasonably often and means some data never loads.
      // We can't fix it by just only initiating the websocket after fetch is complete, because then we miss some
      // update messages entirely (between when we fetch and when we connect the websocket, which happens).
      // We currently fix it by just re-sending the message after 1 second, which seems to work.
      setTimeout(() => {
        this.handleWebSocketMessage(event);
      }, 1000);
      return;
    }

    const message = JSON.parse(event.data);
    if (message.type === 'phrase' && message.data) {
      this.updatePhrase(message.data);

    } else if (message.type === 'summary' && message.data) {
      this.updateSummary(message.data);

    } else if (message.type === 'inflatedUpdate' && message.data) {
      this.updateInflated(message.data);

    } else if (message.type === 'inflatedRefresh' && message.data) {
      this.refreshInflated(message.data);

    }

  };

  updatePhrase = (newPhrase) => {
    this.setState(prevState => {
      const updatedPhrases = { ...prevState.data.phrases };
      updatedPhrases[newPhrase.pk] = newPhrase;
      return {
        data: {
          ...prevState.data,
          phrases: updatedPhrases,
        },
      };
    });
  };

  updateSummary = (newSummary) => {
    this.setState(prevState => ({
      data: {
        ...prevState.data,
        article: {
          ...prevState.data.article,
          summary: newSummary,
        }
      }
    }));
  };

  updateInflated = (newData) => {
    console.log("Updating inflated (i.e. segmentation)")
    this.setState(prevState => ({
      data: {
        ...prevState.data,
        article: {
          ...prevState.data.article,
          source: newData.inflated,
        },
        cps: {
          ...prevState.data.cps,
          ...newData.newCps,
        },
        words: {
          ...prevState.data.words,
          ...newData.newWords,
        },
      }
    }));
  };


  refreshInflated = (newData) => {
    console.log("Rebuilding inflated (i.e. segmentation)")
    this.setState(prevState => ({
      data: {
        ...prevState.data,
        article: {
          ...prevState.data.article,
          source: newData.inflated,
        },
        cps: newData.cps,
        words: newData.words,
      }
    }));
  };

  componentDidMount() {
    this.fetchData();
    this.updateIsMobile();
    window.addEventListener("resize", this.updateIsMobile);

  }

  componentWillUnmount() {
    window.removeEventListener("resize", this.updateIsMobile);
    this.websocket.close();
    this.websocket = null;
  }

  render() {
    return (
      <div className={[
        "reader",
        this.state.isMobile ? '' : 'flex space-x-4 ',
      ].join(' ')}>


        {

          this.state.isMobile &&
          <MobilePanel
            key={this.state.activeItem ? `${this.state.activeItem.type}${this.getActiveObj().pk}` : 0}
            options={this.state.options}
            obj={this.state.activeItem ? this.getActiveObj() : null}
            articlePk={this.props.articlePk}
            cps={this.getActiveWordCPs()}
            currentPhraseObj={this.getCurrentPhraseObj()}

            // For GPT chat
            chatIdentifier={this.getActiveChatIdentifier()}
            phraseObj={this.getCurrentPhraseObj()}
            conversation={this.getActiveConversation()}

            // Methods
            setShowPinyin={this.setShowPinyin}
            setShowToneColors={this.setShowToneColors}
            addChatMessage={this.addChatMessage}

          />


        }

        {
          !this.state.isMobile &&
          <div className="hidden lg:block flex-none w-[200px]">

            <div className="bg-zinc-100 rounded-md p-5 pb-8">
              <h1 className="text-2xl font-bold text-zinc-700">Summary</h1>
              {/*<p className="mt-2 text-sm text-zinc-600">Subheading</p>*/}
              <p className="mt-3 text-zinc-600 text-sm">{this.state.data?.article?.summary || "Loading summary..."}</p>
            </div>


          </div>
        }

        <div className="flex-1">

          <ReaderBody
            data={this.state.data}

            showPinyin={this.state.options.showPinyin}
            showToneColors={this.state.options.showToneColors}
            isMobile={this.state.isMobile}
            isFrozen={this.state.isFrozen}
            activeItem={this.state.activeItem}
            currentPhrase={this.state.currentPhrase}

            // Methods
            setCurrentPhrase={this.setCurrentPhrase}
            setActiveItem={this.setActiveItem}
            clearActiveItem={this.clearActiveItem}
            setIsFrozen={this.setIsFrozen}
            unfreeze={this.unfreeze}
          />

        </div>

        {
          !this.state.isMobile &&
          <div className="reader-sidebar-wrap p-4 pt-0 border-l border-l-zinc-200 flex-none w-[280px]">
            <Sidebar
              type={this.state.activeItem ? this.state.activeItem.type : null}
              options={this.state.options}
              obj={this.state.activeItem ? this.getActiveObj() : null}
              articlePk={this.props.articlePk}
              cps={this.getActiveWordCPs()}
              conversation={this.getActiveConversation()}
              isFrozen={this.state.isFrozen}
              chatIdentifier={this.getActiveChatIdentifier()}
              // Used for GPT chat only
              phraseObj={this.getCurrentPhraseObj()}

              // Methods
              setShowPinyin={this.setShowPinyin}
              setShowToneColors={this.setShowToneColors}
              addChatMessage={this.addChatMessage}

            />
          </div>
        }

      </div>

    )
  }
}

export default Reader


