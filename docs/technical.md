
# Technical Architecture

## System Components



## Request Flow

```mermaid
sequenceDiagram
    participant User
    participant NGINX
    participant Redis
    participant Auth
    participant Provider
    
    User->>NGINX: API Request
    NGINX->>Redis: Check token validity
    Redis-->>NGINX: Token status
    NGINX->>Auth: Validate permissions
    Auth-->>NGINX: Permission status
    NGINX->>Provider: Forward request
    Provider-->>NGINX: Response
    NGINX->>Redis: Log request
    NGINX-->>User: Return response
```

## Core Concepts

```mermaid
classDiagram
    class User {
        +String id
        +String username
        +Group[] groups
        +addGroup(Group group)
        +removeGroup(Group group)
    }

    class Group {
        +String id
        +String name
        +User[] members
        +addUser(User user)
        +removeUser(User user)
    }

    class Token {
        +String id
        +String userId
        +Date createdAt
        +generate()
        +revoke()
    }

    class Route {
        +String path
        +Group[] disabledGroups
        +String[] blacklistWords
        +String~Integer~ quotas
    }

    User "1" *-- "many" Group : belongs to
    Group "1" *-- "many" User : contains
    User "1" *-- "many" Token : manages
    Route "1" *-- "many" Group : disables access for
```
