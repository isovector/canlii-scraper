{-# LANGUAGE NumDecimals       #-}
{-# LANGUAGE LambdaCase        #-}
{-# LANGUAGE OverloadedStrings #-}

module Lib where

import qualified Data.Set as S
import Data.Set (Set)
import Control.Concurrent
import Test.WebDriver
import Test.WebDriver.Commands
import Data.Maybe (fromMaybe, listToMaybe)
import Data.Text (Text)
import qualified Data.Text as T
import Control.Monad (forever, filterM)
import Control.Monad.IO.Class (MonadIO(liftIO))
import Data.Traversable (for)
import Debug.Trace (traceM)
import System.Random
import Data.Foldable



conf :: WDConfig
conf = useBrowser firefox $ defaultConfig

main :: IO ()
main = runSession conf . finallyClose $ prog


prog :: WD ()
prog = do
  openPage "https://www.canlii.org/en/ca/scc/doc/2020/2020scc39/2020scc39.html"
  forever $ do
    els <- useCited `alt` useCitedBy
    liftIO $ threadDelay 1e6
    if S.null els
       then back
       else do
          el <- liftIO $ randomElement els
          click el
          liftIO $ randomRIO (5e6, 20e6) >>= threadDelay


alt :: Monad m => m (Set a) -> m (Set a) -> m (Set a)
alt ma mb = do
  sa <- ma
  case S.null sa of
    False -> pure sa
    True -> mb




useCited :: WD (Set Element)
useCited = useTab "cited-tab" "citedContent" "decision"


useCitedBy :: WD (Set Element)
useCitedBy = useTab "treatment-tab" "citedBy" "name"


randomElement :: Foldable t => t a -> IO a
randomElement t = do
  let els = toList t
      len = length els
  n <- randomRIO (0, len - 1)
  pure $ els !! n


useTab :: Text -> Text -> Text -> WD (Set Element)
useTab tab cid cls = do
  clickTab tab
  liftIO $ threadDelay 2e6
  getSelfLinks cid cls



clickTab :: Text -> WD ()
clickTab tab_id = do
  findElemMaybe (ByCSS $ "#" <> tab_id <> ":not(.disabled)" ) >>= \case
    Just tab_a -> click tab_a
    Nothing    -> pure ()


getSelfLinks :: Text -> Text -> WD (Set Element)
getSelfLinks cid cls = do
  els <- findElems $ ByCSS $ "#" <> cid <> " span." <> cls <> " a"
  fmap S.fromList $ flip filterM els $ \el -> do
    mhref <- attr el "href"
    pure $ case mhref of
      Just href -> and
        [ T.isPrefixOf "https://www.canlii.org/en/" href
        , not $ T.isInfixOf "#" href
        ]
      Nothing -> False


findElemMaybe :: Selector -> WD (Maybe Element)
findElemMaybe = fmap listToMaybe . findElems

