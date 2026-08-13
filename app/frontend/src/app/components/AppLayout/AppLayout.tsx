import imgAvatar from '@app/assets/bgimages/default-user.svg';
import logoStd from '@app/assets/bgimages/Logo-Red_Hat-AI-A-Standard-RGB.svg';
import logoReverse from '@app/assets/bgimages/Logo-Red_Hat-AI-A-Reverse-RGB.svg';
import {
  Avatar,
  Brand,
  Button,
  ButtonVariant,
  Content,
  ContentVariants,
  Dropdown,
  DropdownGroup,
  DropdownItem,
  DropdownList,
  Flex,
  Masthead,
  MastheadBrand,
  MastheadContent,
  MastheadLogo,
  MastheadMain,
  MenuToggle,
  Page,
  Popover,
  SkipToContent,
  ToggleGroup,
  ToggleGroupItem,
  Toolbar,
  ToolbarContent,
  ToolbarGroup,
  ToolbarItem,
} from '@patternfly/react-core';
import { QuestionCircleIcon } from '@patternfly/react-icons';
import MoonIcon from '@patternfly/react-icons/dist/esm/icons/moon-icon';
import SunIcon from '@patternfly/react-icons/dist/esm/icons/sun-icon';
import * as React from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation } from 'react-router-dom';
import { supportedLngs } from '../../../i18n/config';
import { useUser } from '@app/components/UserContext/UserContext';

interface IAppLayout {
  children: React.ReactNode;
}

const AppLayout: React.FunctionComponent<IAppLayout> = ({ children }) => {
  const [selectedLanguage, setSelectedLanguage] = React.useState('en');
  const [isDarkTheme, setIsDarkTheme] = React.useState(false);

  const onChangeLanguage = (_event: React.FormEvent<HTMLSelectElement>, language: string) => {
    setSelectedLanguage(language);
    i18n.changeLanguage(language);
  };

  //i18n
  const { t, i18n } = useTranslation();
  React.useEffect(() => {
    i18n.changeLanguage(selectedLanguage);
  }, [selectedLanguage]);

  // User
  const { userName, setUserName } = useUser();

  React.useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        // Get headers from current page
        const response = await fetch(window.location.href, {
          method: 'HEAD',
          credentials: 'same-origin' // Include cookies in the request
        });

        const entries = [...response.headers.entries()];
        const gapAuthHeader = entries.find(entry => entry[0] === 'gap-auth');
        const gapAuthValue = gapAuthHeader ? gapAuthHeader[1] : 'user@domain.com';
        setUserName(gapAuthValue);
      } catch (error) {
        console.error('Error fetching user info:', error);
      }
    }
    fetchUserInfo();
  }, []);

  const HeaderTools = ({
    isDarkTheme,
    setIsDarkTheme
  }) => {

    const toggleDarkTheme = (_evt, selected) => {
      const darkThemeToggleClicked = !selected === isDarkTheme;
      const htmlElement = document.querySelector('html');
      if (htmlElement) {
        htmlElement.classList.toggle('pf-v6-theme-dark', darkThemeToggleClicked);
      }
      setIsDarkTheme(darkThemeToggleClicked);
    };

    const [isLanguageDropdownOpen, setLanguageDropdownOpen] = React.useState(false);

    return (
      <Toolbar isFullHeight>
        <ToolbarContent>
          <ToolbarGroup align={{ default: 'alignEnd' }}>
            <ToolbarItem>
              <ToggleGroup aria-label="Dark theme toggle group">
                <ToggleGroupItem
                  aria-label="light theme toggle"
                  icon={<SunIcon />}
                  isSelected={!isDarkTheme}
                  onChange={toggleDarkTheme}
                />
                <ToggleGroupItem
                  aria-label="dark theme toggle"
                  icon={<MoonIcon />}
                  isSelected={isDarkTheme}
                  onChange={toggleDarkTheme}
                />
              </ToggleGroup>
            </ToolbarItem>
            <ToolbarItem>
              <Dropdown
                onSelect={() => setLanguageDropdownOpen(!isLanguageDropdownOpen)}
                onOpenChange={(isOpen) => setLanguageDropdownOpen(isOpen)}
                isOpen={isLanguageDropdownOpen}
                toggle={(toggleRef) => (
                  <MenuToggle
                    ref={toggleRef}
                    onClick={() => setLanguageDropdownOpen(!isLanguageDropdownOpen)}
                    isExpanded={isLanguageDropdownOpen}
                  >
                    {supportedLngs[selectedLanguage] || 'en'}
                  </MenuToggle>
                )}
                popperProps={{ position: 'right' }}
              >
                <DropdownGroup key="Language" label="Language">
                  <DropdownList>
                    {Object.entries(supportedLngs).map(([lngCode, lngName], index) => (
                      <DropdownItem key={index} value={lngCode} label={lngName} onClick={() => onChangeLanguage(null as any, lngCode)}>
                        {lngName}
                      </DropdownItem>
                    ))}
                  </DropdownList>
                </DropdownGroup>
              </Dropdown>
            </ToolbarItem>
            <ToolbarItem>
              <Popover
                aria-label="Help"
                position="right"
                headerContent={t('app_header.help.header')}
                bodyContent={t('app_header.help.body')}
                footerContent={t('app_header.help.footer')}
              >
                <Button aria-label="Help" variant={ButtonVariant.plain} icon={<QuestionCircleIcon />} />
              </Popover>
            </ToolbarItem>
            <ToolbarItem>
                <Flex direction={{ default: 'column' }} alignItems={{ default: 'alignItemsCenter' }} justifyContent={{ default: 'justifyContentCenter' }} className='pf-v5-global--spacer--md'>
                <Content component={ContentVariants.p}>
                  {userName}
                </Content>
                </Flex>
            </ToolbarItem>
            <ToolbarItem>
              <Avatar src={imgAvatar} alt="" isBordered className='avatar' />
            </ToolbarItem>
          </ToolbarGroup>
        </ToolbarContent>
      </Toolbar>
    );
  };

  const Header = (
    <Masthead>
      <MastheadMain>
        <MastheadBrand data-codemods>
          <MastheadLogo data-codemods style={{ width: 'auto' }}>
            <Flex direction={{ default: 'row' }} alignItems={{ default: 'alignItemsCenter' }} flexWrap={{ default: 'nowrap' }}>
              <Brand src={!isDarkTheme ? logoStd : logoReverse} alt="Patternfly Logo" heights={{ default: '32px' }} />
              <Content style={{ marginLeft: '1rem' }}>
                <Content component={ContentVariants.h3} className='title-text'>{t('app_header.powered_by')}</Content>
              </Content>
            </Flex>
          </MastheadLogo>
        </MastheadBrand>
      </MastheadMain>
      <MastheadContent>
        <HeaderTools isDarkTheme={isDarkTheme} setIsDarkTheme={setIsDarkTheme} />
      </MastheadContent>
    </Masthead>
  );

  const location = useLocation();

  const pageId = 'primary-app-container';

  const PageSkipToContent = (
    <SkipToContent onClick={(event) => {
      event.preventDefault();
      const primaryContentContainer = document.getElementById(pageId);
      primaryContentContainer && primaryContentContainer.focus();
    }} href={`#${pageId}`}>
      Skip to Content
    </SkipToContent>
  );
  return (
    <Page
      mainContainerId={pageId}
      masthead={Header}
      skipToContent={PageSkipToContent}>
      {children}
    </Page>
  );
};

export { AppLayout };
