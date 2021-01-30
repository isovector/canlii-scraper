{-# LANGUAGE TypeApplications #-}
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
import Data.Char (isDigit)
import Data.Bifunctor (Bifunctor(bimap))
import Data.Bitraversable (bisequence)



conf :: WDConfig
conf = useBrowser firefox $ defaultConfig

main :: IO ()
main = runSession conf . finallyClose $ prog


prog :: WD ()
prog = do
  openPage "https://www.canlii.org/en/ca/scc/doc/1986/1986canlii46/1986canlii46.html"
  forever $ do
    url <- getCurrentURL
    liftIO $ print url
    els <- useBiggerTab
    liftIO $ threadDelay 1e6
    if S.null els
       then back
       else do
          el <- liftIO $ randomElement els
          click el
          liftIO $ randomRIO (2e6, 15e6) >>= threadDelay


alt :: Monad m => m (Set a) -> m (Set a) -> m (Set a)
alt ma mb = do
  sa <- ma
  case S.null sa of
    False -> pure sa
    True -> mb


useBiggerTab :: WD (Set Element)
useBiggerTab = do
  cited_sz    <- getTabSize "cited-tab"
  cited_by_sz <- getTabSize "treatment-tab"

  case useBigger cited_sz cited_by_sz of
    Nothing -> back >> useBiggerTab
    Just x -> fmap (either id id) $ bisequence $ bimap useCited useCitedBy x


useCited :: Element -> WD (Set Element)
useCited = useTab "citedContent" "decision"


useCitedBy :: Element -> WD (Set Element)
useCitedBy = useTab "citedBy" "name"


randomElement :: Foldable t => t a -> IO a
randomElement t = do
  let els = toList t
      len = length els
  n <- randomRIO (0, len - 1)
  pure $ els !! n

useBigger :: Maybe (Int, a) -> Maybe (Int, b) -> Maybe (Either a b)
useBigger (Just (_, e)) Nothing = Just $ Left e
useBigger Nothing (Just (_, e)) = Just $ Right e
useBigger (Just (s1, e1)) (Just (s2, e2)) = Just $
  if s1 > s2
     then Left e1
     else Right e2
useBigger _ _ = Nothing


useTab :: Text -> Text -> Element -> WD (Set Element)
useTab cid cls tab = do
  click tab
  liftIO $ threadDelay 2e6
  getSelfLinks cid cls


getTabSize :: Text -> WD (Maybe (Int, Element))
getTabSize tab_id = do
  findElemMaybe (ByCSS $ "#" <> tab_id <> ":not(.disabled)" ) >>= \case
    Just tab_a -> do
      txt <- getText tab_a
      let size = read @Int $ filter isDigit $ T.unpack txt
      pure $ Just (size, tab_a)
    Nothing    -> pure Nothing



clickTab :: Text -> WD ()
clickTab tab_id = do
  findElemMaybe (ByCSS $ "#" <> tab_id <> ":not(.disabled)" ) >>= \case
    Just tab_a -> do
      txt <- getText tab_a
      let x = read @Int $ filter isDigit $ T.unpack txt
      liftIO $ print x
      click tab_a
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

