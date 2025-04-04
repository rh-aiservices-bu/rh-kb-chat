import imgAvatar from '@app/assets/bgimages/default-user.svg';
import logo from '@app/assets/bgimages/Logo-Red_Hat-OpenShift_AI-A-Reverse-RGB.svg';
import { IAppRoute, IAppRouteGroup, routes } from '@app/routes';
import {
  Avatar,
  Brand,
  Button,
  ButtonVariant,
  FormSelect,
  FormSelectOption,
  Masthead,
  MastheadLogo,
  MastheadContent,
  MastheadMain,
  MastheadToggle, MastheadBrand,
  Nav,
  NavExpandable,
  NavItem,
  NavList,
  Page,
  PageSidebar,
  PageSidebarBody,
  Popover,
  SkipToContent,
  Content,
  ContentVariants,
  Toolbar,
  ToolbarContent,
  ToolbarGroup,
  ToolbarItem
} from '@patternfly/react-core';
import { BarsIcon, QuestionCircleIcon } from '@patternfly/react-icons';
import * as React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { supportedLngs } from '../../../i18n/config';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faLanguage } from '@fortawesome/free-solid-svg-icons';

interface IAppLayout {
  children: React.ReactNode;
}

const AppLayout: React.FunctionComponent<IAppLayout> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const [selectedLanguage, setSelectedLanguage] = React.useState('en');

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
  const [userName, setUserName] = React.useState<string>('');

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
        const gapAuthValue = gapAuthHeader ? gapAuthHeader[1] : '';
        setUserName(gapAuthValue);
        
      } catch (error) {
        console.error('Error fetching user info:', error);
      }
    }
    fetchUserInfo();
  }, []);


  const headerToolbar = (
    <Toolbar id="toolbar" isFullHeight isStatic>
      <ToolbarContent>
        <ToolbarGroup
          variant="action-group-plain"
          align={{ default: "alignEnd" }}
          gap={{ default: "gapMd", md: "gapMd" }}
        >
          <ToolbarItem>
            <FontAwesomeIcon icon={faLanguage} className='language-icon'/>
          </ToolbarItem>
          <ToolbarItem>
            <FormSelect
              value={selectedLanguage}
              onChange={onChangeLanguage}
              aria-label="FormSelect Input"
              ouiaId="BasicFormSelectLanguage"
              className='version-language-select'
            >
              {Object.entries(supportedLngs).map(([lngCode, lngName], index) => (
                <FormSelectOption key={index} value={lngCode} label={lngName} />
              ))}
            </FormSelect>
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
        </ToolbarGroup>
        <ToolbarItem>
          <Content>
            <Content component={ContentVariants.p} className='pf-v5-global--spacer--md'>
              {userName}
            </Content>
          </Content>
        </ToolbarItem>
        <ToolbarItem>
          <Avatar src={imgAvatar} alt="" isBordered className='avatar' />
        </ToolbarItem>
      </ToolbarContent>
    </Toolbar>
  );

  const Header = (
    <Masthead>
      
      <MastheadMain><MastheadToggle hidden={true}>
        <Button icon={<BarsIcon/>} variant="plain" onClick={() => setSidebarOpen(!sidebarOpen)} aria-label="Global navigation" />
      </MastheadToggle>
        <MastheadBrand data-codemods><MastheadLogo data-codemods>
          <Brand src={logo} alt="Patternfly Logo" heights={{ default: '36px' }} />
          <Content style={{ marginLeft: '1rem' }}>
            <Content component={ContentVariants.h3} className='title-text'>{t('app_header.powered_by')}</Content>
          </Content>
        </MastheadLogo></MastheadBrand>
      </MastheadMain>
      <MastheadContent>
        {headerToolbar}
      </MastheadContent>
    </Masthead>
  );

  const location = useLocation();


  const renderNavItem = (route: IAppRoute, index: number) => (
    <NavItem key={`${route.label}-${index}`} id={`${route.label}-${index}`} isActive={route.path === location.pathname} className='navitem-flex'>
      <NavLink exact={route.exact} to={route.path} className={route.path !== '#' ? '' : 'disabled-link'}>
        {t(route.label as string)}
      </NavLink>
    </NavItem>
  );

  const renderNavGroup = (group: IAppRouteGroup, groupIndex: number) => (
    <NavExpandable
      key={`${group.label}-${groupIndex}`}
      id={`${group.label}-${groupIndex}`}
      title={group.label}
      isActive={group.routes.some((route) => route.path === location.pathname)}
    >
      {group.routes.map((route, idx) => route.label && renderNavItem(route, idx))}
    </NavExpandable>
  );

  const Navigation = (
    <Nav id="nav-first-simple" >
      <NavList id="nav-list-first-simple">
        {routes.map(
          (route, idx) => route.label && (!route.routes ? renderNavItem(route, idx) : renderNavGroup(route, idx))
        )}
      </NavList>
    </Nav>
  );

  const Sidebar = (
    <PageSidebar  >
      <PageSidebarBody isFilled>
        {Navigation}
      </PageSidebarBody>
    </PageSidebar>
  );

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
      sidebar={sidebarOpen && Sidebar}
      skipToContent={PageSkipToContent}>
      {children}
    </Page>
  );
};

export { AppLayout };
