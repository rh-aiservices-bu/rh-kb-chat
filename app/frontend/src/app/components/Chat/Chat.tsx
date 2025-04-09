import config from '@app/config';
import { faCommentDots, faPaperPlane } from '@fortawesome/free-regular-svg-icons';
import { faPlusCircle } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { Button, Card, CardBody, CardHeader, Flex, FlexItem, FormSelect, FormSelectOption, Grid, GridItem, Page, PageSection, Panel, PanelMain, PanelMainBody, Stack, StackItem, Content, TextArea, ContentVariants, Tooltip, Bullseye, DropdownList, DropdownItem } from '@patternfly/react-core';
import * as React from 'react';
import { useTranslation } from 'react-i18next';
import { Query, MessageContent } from './classes';
import ChatAnswer, { ChatAnswerRef } from './ChatAnswer'
import githubLogo from '@app/assets/bgimages/github-mark.svg';
import githubLogoWhite from '@app/assets/bgimages/github-mark-white.svg';
import starLogo from '@app/assets/bgimages/star.svg';
import starLogoWhite from '@app/assets/bgimages/star-white.svg';
import { ChatbotFooter, ChatbotFootnote, } from '@patternfly/chatbot/dist/dynamic/ChatbotFooter';
import { MessageBar } from '@patternfly/chatbot/dist/dynamic/MessageBar';
import { Chatbot, ChatbotContent, ChatbotDisplayMode, ChatbotHeader, ChatbotHeaderActions, ChatbotHeaderMain, ChatbotHeaderSelectorDropdown, ChatbotHeaderTitle } from '@patternfly/chatbot';


interface ChatProps {
}

/**
 * Represents the Chat component.
 *
 * @component
 * @param {Object} props - The component props.
 * @returns {JSX.Element} The rendered Chat component.
 */
const Chat: React.FunctionComponent<ChatProps> = () => {

  type CollectionVersion = {
    version_number: string;
  }

  type Collection = {
    collection_base_name: string;
    collection_full_name: string;
    versions: CollectionVersion[];
    language: string;
  };

  const [isDarkTheme, setIsDarkTheme] = React.useState<boolean>(document.documentElement.classList.contains('pf-v6-theme-dark'));
  React.useEffect(() => {
    // Create a MutationObserver to watch for changes to the class list of the body element
    const observer = new MutationObserver(() => {
      setIsDarkTheme(document.documentElement.classList.contains('pf-v6-theme-dark'));
    });

    // Observe the body element for class attribute changes
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });

    // Cleanup the observer when the component unmounts
    return () => observer.disconnect();
  }, []);

  // ChatAnswer Refs
  const childRefs = React.useRef<(ChatAnswerRef | null)[]>([]);

  // Maximum number of ChatAnswer instances
  const searchParams = new URLSearchParams(window.location.search);
  const maxChats = parseInt(searchParams.get('maxchat') || '4', 10);

  // ChatAnswer instances
  const [items, setItems] = React.useState<JSX.Element[]>([
    <ChatAnswer key={1} ref={(el) => (childRefs.current[1] = el)} />
  ]);
  const addItem = () => {
    if (items.length < maxChats) {
      const newItem = (
        <ChatAnswer key={items.length + 1} ref={(el) => (childRefs.current[items.length + 1] = el)} />
      );
      setItems([...items, newItem]);
    }
  };
  const removeItem = () => {
    setItems(items.slice(0, -1));
  };

  //i18n
  const { t, i18n } = useTranslation();

  // Fetch GitHub stars and forks 
  const [repoStars, setRepoStars] = React.useState<number | null>(null);
  React.useEffect(() => {
    fetch('https://api.github.com/repos/rh-aiservices-bu/rh-kb-chat')
      .then((response) => response.json())
      .then((data) => {
        setRepoStars(data.stargazers_count);
      })
      .catch((error) => {
        console.error('Failed to fetch GitHub stars:', error);
      });
  }, []);

  // Collection elements
  const [collections, setCollections] = React.useState<Collection[]>([]); // The collections
  const [collectionFullName, setCollectionFullName] = React.useState<string>('None'); // The selected collection name
  const [versions, setVersions] = React.useState<CollectionVersion[]>([]); // The versions for this collection
  const [selectedVersion, setSelectedVersion] = React.useState<string>(''); // The selected version
  const [selectedCollection, setSelectedCollection] = React.useState<string>('none'); // Default collection name

  // Chat elements
  const [queryText, setQueryText] = React.useState<Query>(new Query('')); // The query text


  // Loads the collections from the backend on startup
  React.useEffect(() => {
    const fetchCollections = async () => {
      const response = await fetch(`${config.backend_api_url}/collections`);
      const data = await response.json();
      setCollections(data);
      setCollectionFullName(data[0].collection_full_name);
      setVersions(data[0].versions);
      setSelectedVersion(data[0].versions[0].version_number);
      setSelectedCollection((data[0].collection_base_name + '_' + data[0].versions[0].version_number).replace(/[.-]/g, '_'));
    }
    fetchCollections();
  }, []);


  /**
   * Sends the query text to the server via WebSocket.
   * Saves the previous response, sources, query, and message history, and create a new Message History from them.
   * Clears the query text, previous response, and previous sources.
   * If the query text is empty, sets the previous response to ['Please enter a query...'].
   */
  const sendQueryText = (message: string | number) => {
    const queryText = String(message);
    const previousQuery = new MessageContent(new Query(queryText)); // Save the previous query
    setQueryText(new Query('')); // Clear the query text
    const query = new Query(queryText, selectedCollection, collectionFullName, selectedVersion, i18n.language);

    if (queryText !== "") {
      childRefs.current.forEach((childRef) => {
        if (childRef) {
          childRef.sendQuery(query);
        }
      });
    }
  }

  /**
   * Updates the collection based on the selected collection and version.
   * @param selectedCollection - The selected collection.
   * @param selectedVersion - The selected version.
   */
  const updateCollection = (selectedCollection: Collection, selectedVersion: string) => {
    setVersions(selectedCollection.versions);
    setSelectedVersion(selectedVersion);
    let collection_name = selectedCollection.collection_base_name + '_' + selectedVersion;
    setSelectedCollection(collection_name.replace(/[.-]/g, '_'));
  }

  /**
   * Handles the change event of the product select element.
   * @param _event - The form event object.
   * @param value - The selected value from the product select element.
   */
  const onChangeProduct = (_event: React.FormEvent<HTMLSelectElement>, value: string) => {
    setCollectionFullName(value);
    const collection = collections.find(collection => collection.collection_full_name === value);
    if (collection) {
      const version = collection.versions[0].version_number;
      updateCollection(collection, version);
      childRefs.current.forEach((childRef) => {
        if (childRef) {
          childRef.changeCollectionOrVersion(collection, version);
        }
      });
    }
  }

  /**
   * Handles the change event of the version select element.
   * 
   * @param _event - The form event object.
   * @param value - The selected value from the version select element.
   */
  const onChangeVersion = (_event: React.FormEvent<HTMLSelectElement>, value: string) => {
    setSelectedVersion(value);
    const collection = collections.find(collection => collection.collection_full_name === collectionFullName);
    if (collection) {
      const version = value;
      updateCollection(collection, version);
      childRefs.current.forEach((childRef) => {
        if (childRef) {
          childRef.changeCollectionOrVersion(collection, version);
        }
      });
    }
  }

  function resetMessageHistory(): void {
    childRefs.current.forEach((childRef) => {
      if (childRef) {
        childRef.resetMessageHistory();
      }
    });
  }

  return (
    <PageSection hasBodyWrapper={false}>
      <Flex direction={{ default: 'column' }}>

        {/* Product, version and language selectors */}
        <FlexItem>
          <Flex>
            <FlexItem>
              <Flex direction={{ default: 'row' }}>
                <FlexItem className='collection-version-language-legends' >
                  <Content>
                    <Content component={ContentVariants.h3} >{t('chat.filter.product')}:</Content>
                  </Content>
                </FlexItem>
                <FlexItem>
                  <FormSelect
                    value={collectionFullName}
                    onChange={onChangeProduct}
                    aria-label="FormSelect Input"
                    ouiaId="BasicFormSelectCategory"
                    className="collection-select"
                  >
                    {collections && collections.map((collection, index) => (
                      <FormSelectOption key={index} value={collection.collection_full_name} label={collection.collection_full_name} />
                    ))}
                  </FormSelect>
                </FlexItem>
              </Flex>
            </FlexItem>
            <FlexItem>
              <Flex direction={{ default: 'row' }}>
                <FlexItem className='collection-version-language-legends'>
                  <Content>
                    <Content component={ContentVariants.h3} >{t('chat.filter.version')}:</Content>
                  </Content>
                </FlexItem>
                <FlexItem>
                  <FormSelect
                    value={selectedVersion}
                    onChange={onChangeVersion}
                    aria-label="FormSelect Input"
                    ouiaId="BasicFormSelectCategory"
                    className='version-language-select'
                  >
                    {versions && versions.map((version, index) => (
                      <FormSelectOption key={index} value={version.version_number} label={version.version_number} />
                    ))}
                  </FormSelect>
                </FlexItem>
              </Flex>
            </FlexItem>
          </Flex>
        </FlexItem>

        {/* Chat Window */}
        <FlexItem className='chat'>
          <Chatbot displayMode={ChatbotDisplayMode.embedded} >
            <ChatbotHeader className='chat-header'>
              <ChatbotHeaderMain>
                <ChatbotHeaderTitle className='chat-header-title'>
                  <Bullseye>
                    <Content>
                      <Content component={ContentVariants.h3} className='chat-header-title'>
                        <FontAwesomeIcon icon={faCommentDots} />&nbsp;{t('chat.title')}
                      </Content>
                    </Content>
                  </Bullseye>
                </ChatbotHeaderTitle>
              </ChatbotHeaderMain>
              <ChatbotHeaderActions>
                <Flex>
                  <FlexItem>
                    <Button onClick={addItem} variant="primary">
                      Add LLM
                    </Button>
                  </FlexItem>
                  <FlexItem>
                    <Button onClick={removeItem} variant="danger" isDisabled={items.length === 0}>
                      Remove last LLM
                    </Button>
                  </FlexItem>
                </Flex>
              </ChatbotHeaderActions>
            </ChatbotHeader>
              <Grid hasGutter
                className="chat-grid">
                {items.map((item, index) => (
                  <GridItem key={index} className='chat-grid-item' span={Math.floor(12 / (items.length)) as any}>
                    {/* Replace with your ChatAnswer component */}
                    {item}
                  </GridItem>
                ))}
              </Grid>
            <ChatbotFooter className='chat-footer'>
              <MessageBar
                hasMicrophoneButton
                hasAttachButton
                onSendMessage={sendQueryText}
              />
            </ChatbotFooter>
          </Chatbot>
        </FlexItem>
        <FlexItem>
          <Stack>
            {/* Disclaimer section */}
            <StackItem>
              <Content component="p" className='chat-disclaimer'>{t('chat.disclaimer1')} {t('chat.disclaimer2')}<br />
                PoC App by <a href='http://red.ht/cai-team' target='_blank'>red.ht/cai-team</a>&nbsp;&nbsp;-&nbsp;&nbsp;
                <a href='https://github.com/rh-aiservices-bu/rh-kb-chat' target='_blank'>Source</a>&nbsp;&nbsp;
                <img src={isDarkTheme ? githubLogoWhite : githubLogo} alt="GitHub Logo" style={{ height: '15px', marginRight: '0.5rem', verticalAlign: 'text-top' }} />
                <span style={{ textDecoration: 'none', color: 'inherit' }}>{repoStars !== null ? `${repoStars}` : ''}&nbsp;</span>
                {repoStars !== null &&
                  <img src={isDarkTheme ? starLogoWhite : starLogo} alt="Star Logo" style={{ height: '15px', marginRight: '0.5rem', verticalAlign: 'text-top' }} />
                }
              </Content>
            </StackItem>
          </Stack>

        </FlexItem>
      </Flex>
    </PageSection>
  );
}

export { Chat };
