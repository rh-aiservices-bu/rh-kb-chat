import config from '@app/config';
import { faCommentDots, faPaperPlane } from '@fortawesome/free-regular-svg-icons';
import { faPlusCircle } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { Button, Card, CardBody, CardHeader, Flex, FlexItem, FormSelect, FormSelectOption, Grid, GridItem, Page, PageSection, Panel, PanelMain, PanelMainBody, Stack, StackItem, Content, TextArea, ContentVariants, Tooltip } from '@patternfly/react-core';
import * as React from 'react';
import { useTranslation } from 'react-i18next';
import { Query, Message } from './classes';
import ChatAnswer, { ChatAnswerRef } from './ChatAnswer'

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
  const sendQueryText = () => {
    const previousQuery = new Message(new Query(queryText.content)); // Save the previous query
    setQueryText(new Query('')); // Clear the query text
    const query = new Query(queryText.content, selectedCollection, collectionFullName, selectedVersion, i18n.language);

    if (query.content !== "") {
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
        <FlexItem className='flex-chat'>
          <Card className='chat-card'>
            <CardHeader className='chat-card-header'>
              <Flex justifyContent={{ default: 'justifyContentSpaceBetween' }}>
                <FlexItem>
                  {/* Empty item to center title */}
                </FlexItem>
                <FlexItem>
                  <Content>
                    <Content component={ContentVariants.h3} className='chat-card-header-title'>
                      <FontAwesomeIcon icon={faCommentDots} />&nbsp;{t('chat.title')}
                    </Content>
                  </Content>
                </FlexItem>
                <FlexItem>
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
                </FlexItem>
              </Flex>
            </CardHeader>
            <CardBody className='chat-card-body'>
              <Stack>
                {/* ChatbotAnswer panels */}
                <StackItem isFilled className='chat-bot-answer' id='chatBotAnswer'>
                  <Grid hasGutter
                    className="chat-grid">
                    {items.map((item, index) => (
                      <GridItem key={index} className='chat-grid-item' span={Math.floor(12 / (items.length)) as any}>
                        {/* Replace with your ChatAnswer component */}
                        {item}
                      </GridItem>
                    ))}
                  </Grid>
                </StackItem>

                {/* Input section */}
                <StackItem className='chat-input-panel'>
                  <Panel variant="raised">
                    <PanelMain>
                      <PanelMainBody className='chat-input-panel-body'>
                        <TextArea
                          value={queryText.content}
                          type="text"
                          onChange={event => {
                            setQueryText({ ...queryText, content: event.target.value });
                          }}
                          aria-label="query text input"
                          placeholder={t('chat.placeholder')}
                          onKeyDown={event => {
                            if (event.key === 'Enter') {
                              event.preventDefault();
                              sendQueryText();
                            }
                          }}
                        />
                        <Flex>
                          <FlexItem>
                            <Tooltip
                              content={<div>{t('chat.new_chat')}</div>}
                            >
                              <Button variant="link" onClick={resetMessageHistory} aria-label='StartNewChat'><FontAwesomeIcon icon={faPlusCircle} /></Button>
                            </Tooltip>
                          </FlexItem>
                          <FlexItem align={{ default: 'alignRight' }}>
                            <Tooltip
                              content={<div>{t('chat.send')}</div>}
                            >
                              <Button variant="link" onClick={sendQueryText} aria-label='SendQuery'><FontAwesomeIcon icon={faPaperPlane} /></Button>
                            </Tooltip>
                          </FlexItem>

                        </Flex>
                      </PanelMainBody>
                    </PanelMain>
                  </Panel>
                </StackItem>
                <StackItem>
                  <Content>
                    <Content component="p" className='chat-disclaimer'>{t('chat.disclaimer1')}<br />{t('chat.disclaimer2')}</Content>
                  </Content>
                </StackItem>
              </Stack>
            </CardBody>
          </Card >
        </FlexItem>
      </Flex>
    </PageSection>
  );
}

export { Chat };
