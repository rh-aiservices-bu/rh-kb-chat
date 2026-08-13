import { NotFound } from '@app/components/NotFound/NotFound';
import { useDocumentTitle } from '@app/utils/useDocumentTitle';
import * as React from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { Chat } from './components/Chat/Chat';


export interface IAppRoute {
  label?: string; // Excluding the label will exclude the route from the nav sidebar in AppLayout
  element: JSX.Element;
  path: string;
  title: string;
  routes?: undefined;
  bottomRoutes?: undefined;
  disabled?: boolean;
}

export interface IAppRouteGroup {
  label: string;
  routes: IAppRoute[];
}

export type AppRouteConfig = IAppRoute | IAppRouteGroup;


const routes: AppRouteConfig[] = [
  {
    element: <Navigate to="/Chat" replace/>,
    path: '/',
    title: 'Redirect',
  },
  {
    element: <Chat />,
    label: 'app_menu.chat_documentation',
    path: '/Chat',
    title: 'app_menu.chat_documentation',
  }
];


const flattenedRoutes: IAppRoute[] = routes.reduce(
  (flattened, route) => [...flattened, ...(route.routes ? route.routes : [route])],
  [] as IAppRoute[]
);

const AppRoutes = (): React.ReactElement => (
  <Routes>
    {flattenedRoutes.map((route, idx) => (
      <Route path={route.path} element={route.element} key={idx} />
    ))}
    <Route element={<NotFound/>} />
  </Routes>
);

export { AppRoutes, routes };
