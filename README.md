# Bootstrap API 기반 동적 UI 검증 보고서

## 1. 검증 결과

**서버에서 전달한 Bootstrap 설정으로 화면, 내비게이션과 화면 이동을 구성할 수 있음을 확인했습니다.**

현재 검증에서는 실제 서버 응답과 같은 형식의 로컬 JSON을 서버 응답으로 가정하여 `fetch`했습니다. 클라이언트는 응답의 `routes`, `pages`, `bottomNavigation`을 해석하여 UI를 구성합니다.

## 2. 화면 구성

**서버가 Route와 컴포넌트 정보를 내려주면 클라이언트가 해당 화면을 동적으로 구성합니다.**

화면을 구성하는 배너, 빠른 메뉴, 행사 목록과 공지 목록은 모두 컴포넌트입니다. 이하에서는 각 항목을 `컴포넌트(배너)`, `컴포넌트(빠른 메뉴)`, `컴포넌트(행사 목록)`, `컴포넌트(공지 목록)`으로 표기합니다.

```json
{
  "routes": [
    {
      "id": "route-home",
      "path": "/",
      "pageType": "HOME",
      "enabled": true
    }
  ],
  "pages": [
    {
      "routeId": "route-home",
      "pageType": "HOME",
      "components": [
        {
          "id": "main-banner",
          "componentType": "BANNER",
          "visible": true,
          "sortOrder": 1,
          "props": { "title": "축제 안내" }
        },
        {
          "id": "quick-menu",
          "componentType": "QUICK_MENU",
          "visible": true,
          "sortOrder": 2,
          "props": { "title": "바로가기" }
        },
        {
          "id": "event-list",
          "componentType": "EVENT_LIST",
          "visible": true,
          "sortOrder": 3,
          "props": {
            "title": "주요 행사",
            "dataSourceKey": "FEATURED_EVENTS"
          }
        }
      ]
    }
  ]
}
```

### 2.1 화면 유형 선택

**클라이언트는 `pageType` 값으로 먼저 전체 화면 유형을 선택합니다.**

`HOME`과 `CONTENT`는 클라이언트에 정의된 전용 페이지 레이아웃 없이, 공통 컨테이너 안에 서버의 `components` 배열을 배치하여 화면을 동적으로 구성합니다.

`MAP`과 `SCHEDULE`은 클라이언트에 미리 구현된 지도 화면과 일정 화면을 표시합니다. 현재 검증 코드에서는 이 전용 화면에 서버 컴포넌트를 추가로 배치하지 않습니다.

```tsx
switch (route.pageType) {
  case "HOME":
  case "CONTENT": return <ConfiguredPage route={route} />;
  case "MAP": return <MapPage route={route} />;
  case "SCHEDULE": return <SchedulePage route={route} />;
}
```

이 단계는 어떤 화면을 표시할지 결정하는 과정입니다. 다음의 컴포넌트 구성 단계는 현재 `HOME`과 `CONTENT` 화면에 적용됩니다.

### 2.2 화면 내부 컴포넌트 구성

**선택된 화면 내부에서는 서버가 내려준 `components` 배열로 여러 컴포넌트를 구성합니다.**

`components` 배열에서 `visible`이 `true`인 항목만 선택하고 `sortOrder` 순서로 정렬한 후, `map`으로 순회하여 화면에 배치합니다.

```tsx
interface DynamicComponentListProps {
  components: PageComponentConfig[];
}

function DynamicComponentList(props: DynamicComponentListProps) {
  const { components } = props;

  // 노출 대상만 선택하고 서버에서 지정한 순서로 정렬합니다.
  const visibleComponents = [...components]
    .filter((component) => component.visible)
    .sort(
      (left, right) =>
        left.sortOrder - right.sortOrder ||
        left.id.localeCompare(right.id),
    );

  // 정렬된 배열을 순회하여 각 항목을 화면 컴포넌트로 구성합니다.
  return visibleComponents.map((component) => (
    <DynamicComponentRenderer
      key={component.id}
      component={component}
    />
  ));
}
```

반복 처리된 각 항목은 `componentType`에 따라 실제 화면 컴포넌트로 변환됩니다.

```tsx
switch (component.componentType) {
  case "BANNER": return <BannerComponent component={component} />;
  case "QUICK_MENU": return <QuickMenuComponent component={component} />;
  case "EVENT_LIST": return <EventListComponent component={component} />;
  case "NOTICE_LIST": return <NoticeListComponent component={component} />;
}
```

예를 들어 서버에서 위와 같이 컴포넌트 3개를 내려주면 `map`을 통해 컴포넌트(배너), 컴포넌트(빠른 메뉴), 컴포넌트(행사 목록)가 `sortOrder` 순서로 화면에 구성됩니다.

따라서 서버 설정을 변경하면 클라이언트 코드를 수정하지 않고 화면 종류와 컴포넌트 구성을 변경할 수 있습니다.

## 3. 바텀 내비게이션 구성

**바텀 내비게이션에서는 서버가 내려주는 설정으로 여러 메뉴 아이템을 구성할 수 있습니다.**

아래 코드와 같이 각 아이템의 문구, 연결할 Route, 출력 순서와 노출 여부를 지정할 수 있습니다.

```json
{
  "bottomNavigation": {
    "enabled": true,
    "items": [
      {
        "id": "nav-home",
        "label": "홈",
        "routeId": "route-home",
        "sortOrder": 1,
        "enabled": true
      },
      {
        "id": "nav-map",
        "label": "행사장",
        "routeId": "route-map",
        "sortOrder": 2,
        "enabled": true
      },
      {
        "id": "nav-program",
        "label": "프로그램",
        "routeId": "route-schedule",
        "sortOrder": 3,
        "enabled": true
      }
    ]
  }
}
```

클라이언트는 활성화된 아이템만 `sortOrder` 순서로 정렬한 후, `items.map()`으로 배열을 순회하면서 각 아이템을 하나의 링크로 생성합니다. 각 링크의 이동 경로는 `routeId`와 일치하는 Route에서 가져옵니다.

```tsx
{items.map(({ item, route, selected }) => (
  <Link
    key={item.id}
    to={route.path}
    aria-current={selected ? "page" : undefined}
  >
    {item.label}
  </Link>
))}
```

예를 들어 서버 응답에 아이템이 3개 있으면 `map`이 3번 처리되어 홈, 행사장, 프로그램 링크가 각각 생성됩니다. 따라서 서버 설정으로 메뉴 개수, 문구, 순서, 노출 여부, 이동 경로와 현재 메뉴 표시를 관리할 수 있습니다.

## 4. 컴포넌트 클릭에 따른 화면 이동

**화면 컴포넌트의 링크 클릭은 서버가 지정한 `routeId`를 기준으로 다른 화면에 연결됩니다.**

```json
{
  "componentType": "QUICK_MENU",
  "props": {
    "items": [
      {
        "label": "행사장 안내",
        "routeId": "route-map"
      }
    ]
  }
}
```

클라이언트는 `routeId`로 활성 Route를 찾고 React Router 링크를 생성합니다.

```tsx
const route = bootstrap.routes.find(
  (candidate) => candidate.id === item.routeId && candidate.enabled,
)!;

return <Link to={route.path}>{item.label}</Link>;
```

클릭하면 URL이 변경되고, 변경된 URL에 맞는 `pageType` 화면이 다시 선택됩니다. 바텀 내비게이션의 선택 상태도 함께 갱신됩니다.

컴포넌트가 URL을 직접 갖지 않고 `routeId`를 참조하므로, 서버에서 Route 경로를 변경해도 동일한 Route ID를 유지하면 컴포넌트 수정 없이 새 경로로 이동할 수 있습니다.

## 5. 결론 및 보완 사항

**Bootstrap API를 중심으로 화면과 내비게이션을 구성하고, 컴포넌트 이벤트를 화면 이동으로 연결하는 방식은 적용 가능한 것으로 확인했습니다.**

실제 서비스 적용 전에는 서버 응답 스키마 검증, 통신 오류 처리, 존재하지 않는 `routeId` 처리와 브라우저 기반 클릭 테스트를 추가해 주시는 것이 좋습니다.
