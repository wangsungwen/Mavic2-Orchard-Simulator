// Copyright 1998-2017 Epic Games, Inc. All Rights Reserved.

#include "Blocks.h"

#include "Modules/ModuleManager.h"

#include "NavigationPicker.h"
#include "Engine/World.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

class FBlocksModule : public FDefaultGameModuleImpl
{
    FDelegateHandle Handle;
public:
    virtual void StartupModule() override {
        Handle = FWorldDelegates::OnWorldInitializedActors.AddLambda([](const UWorld::FActorsInitializedParams& Params) {
            if (Params.World && Params.World->IsGameWorld() && FParse::Param(FCommandLine::Get(), TEXT("PointNavigation")))
                Params.World->SpawnActor<ANavigationPicker>();
        });
    }
    virtual void ShutdownModule() override {
        FWorldDelegates::OnWorldInitializedActors.Remove(Handle);
    }
};
IMPLEMENT_PRIMARY_GAME_MODULE(FBlocksModule, Blocks, "Blocks");
